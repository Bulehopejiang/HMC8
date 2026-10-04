# my_tkui.py
# ==============================
# 自制Tkinter简易中间件库（MyTkUI）
# 核心设计：统一 .add() 接口，支持无限嵌套布局，封装原生tkinter
# 规则：所有容器都使用 容器.add(控件, expand=?) 添加子元素
# expand=True：控件铺满所在容器/格子，窗口缩放自动拉伸（编辑器、日志面板、分栏容器）
# expand=False（默认）：控件保持自身需要的大小，不被拉伸（文件选择框、按钮）
#   备注 1：本库自己的控件（LogPanel、分栏容器、FileSelect、MyButton）天生就属于
#          其中一类，所以一般不用手写 expand：LogPanel 和分栏容器自动铺满，
#          FileSelect / MyButton 自动保持自身大小。原生控件（tk.Button 等）才需要显式指定。
#   备注 2：在分栏容器的格子（.left/.right/.top/.bottom）里也遵守同一套规则 ——
#          会铺满的控件充满整个格子；固定尺寸的控件只占自身大小，
#          格子也不会为它膨胀，所以控件周围不会留出一片空白。
#
# 可用控件清单：
#   AppWindow()      # 顶层主窗口
#   HSplitFrame()    # 水平左右分栏容器，提供 .left / .right 子容器
#                     # proportional=True(默认)：左右宽度严格等于权重之比
#                     # proportional=False：左侧保持控件自然宽度，多余宽度按权重给右侧
#   VSplitFrame()    # 垂直上下分栏容器，提供 .top / .bottom 子容器
#                     # proportional=True(默认)：上下高度严格等于权重之比（默认3:1），
#                     #   窗口最大化/缩放、字体缩放后比例都不变，不会失衡
#                     # proportional=False：先满足上下两块的固有高度，剩余空间再按权重分
#   # 说明：两种分栏的 proportional=True 都是"无缝切分"——
#   #   子单元格铺满容器，中间不留空隙、边缘不留白边，比例严格等于权重之比；
#   #   想要分栏之间存在间隙，用 gap= 参数指定（默认 0 = 无缝）；
#   #   运行时改比例用 split.set_weights(a, b)
#   LogPanel()       # 多行文本面板（代码编辑器 / 日志输出 / 只读展示）【快捷键、字体颜色】
#                     # Ctrl滚轮缩放只改字号，不会改变控件占用空间，父容器布局不会被撑坏
#                     # Ctrl+Z 撤销 / Ctrl+Y 重做（只读面板上这两个键不生效）
#                     # read_only=True 时用户只能查看、选中、复制，不能编辑：
#                     #   LogPanel(master, read_only=True) 或 panel.set_read_only(True)
#   AppShell()       # 应用骨架：顶部操作区 + 中间内容区 + 底部状态栏
#                     #   属性 .top / .content / .bottom（都是支持 .add() 的子容器）
#   ActionBar()      # 横向操作条（工具栏/按钮行）：add_button / add_label / add_entry /
#                     #   add_space / add_separator；靠右排用 bar.to_end = True
#   StatusBar()      # 底部状态栏：set() 改文字、set_right() 放补充信息、
#                     #   flash() 临时提示后自动恢复
#   PageBook()       # 多页签容器：add_page(标题) 得到页面容器、show(标题) 切页
#   DialogBox()      # 通用表单对话框：填若干项，show() 返回 {键: 值} 字典
#                     #   （CommitDialog 是它的另一个名字，用法一样）
#   FileSelect()     # 文件选择控件：标签+输入框+选择按钮
#   MyButton()       # 按钮控件，点击触发回调
# ==============================
import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog, scrolledtext
from pathlib import Path
import re
import threading
from typing import Callable, Optional, Any


def safe_call(root: tk.Tk, func: Callable, *args, **kwargs) -> bool:
    """
    【线程安全UI调度工具函数】
    tkinter 禁止子线程直接操作UI控件。
    在子线程内调用此函数，把UI任务投递到主线程执行。
    参数：
        root: 主窗口tk对象
        func: 需要执行的UI函数
        *args,**kwargs: func对应的参数
    返回：
        True=任务已成功排队；False=投递不成功（窗口已关闭 /
        主线程还没进 mainloop），此时任务被丢弃，调用方无需处理。
    说明：
        投递不成功时**不会抛异常**。子线程里往界面写日志本来就是"尽力而为"，
        抛异常只会把干活线程打断，反而更难查问题。
        这里要同时挡两种异常：
            TclError     —— 窗口已经销毁；
            RuntimeError —— after() 需要注册一条 Tcl 命令，而主线程还没进
                            mainloop（例如界面刚建好、还没调 mainloop 时，
                            或者程序自己在用 update() 手动跑事件循环）。
    """
    try:
        root.after(0, lambda: func(*args, **kwargs))
        return True
    except (tk.TclError, RuntimeError):
        return False


# 分栏容器左右/上下两个单元格之间的间隙（像素）。
# 默认 0：两个单元格无缝拼接，容器空间被完全用满，不出现任何"多余的空隙"。
# 如果希望两块面板之间有一条明显的分界线，构造分栏容器时传 gap=6 之类的值即可。
_DEFAULT_SPLIT_GAP = 0

# 【内部】复合控件标记：带这个属性的控件被 add() 添加时，会自动铺满所在格子。
# 本库自己的控件都带它，_is_filling() 就不必逐个列举类型名 ——
# 以后新增控件只要在类里写一行 `_mytkui_composite = True` 即可，不会漏。
_COMPOSITE_ATTR = "_mytkui_composite"


def _size_policy(widget: tk.Widget, expand: bool):
    """
    【内部工具函数】把"是否拉伸"翻译成 grid 的 sticky 与权重。

    统一用 sticky="nsew" + 列权重 1 表达"拉伸"：
        拉伸   → 格子有多大就铺多大（宽高都撑满）
        不拉伸 → sticky="ew"，宽度跟着格子走（这样工具栏里的按钮会等宽排开），
                 高度保持自身需要的高度（不会被拉成一整条）
    参数：
        widget: 子控件（保留参数，便于以后按控件类型细分）
        expand: 是否拉伸
    返回：
        (sticky, weight) 二元组
    """
    return ("nsew", 1) if expand else ("ew", 0)


def safe_write_text(path: str, content: str, encoding: str = "utf-8") -> str:
    """
    【工具函数】安全写文本文件：先写临时文件、写完整了再替换目标文件。

    为什么需要它：
        直接 open(path,'w') 会先把文件清空再写。如果写入过程中出问题
        （内容里有非法字符、文件被别的程序占用、磁盘写满……），
        磁盘上就留下一个 0 字节的空文件，看起来正是"文件建好了但内容没写进去"。
        本函数改成"先写同目录下的临时文件 → 成功后再替换"，
        于是要么目标文件是完整的新内容，要么保持原样，不会出现半截空文件。
    参数：
        path: 目标文件路径
        content: 要写入的文本
        encoding: 文件编码，默认 utf-8
    返回：
        出错原因字符串；成功时返回 ""（空字符串）
    """
    target = (path or "").strip()
    if not target:
        return "文件路径为空"
    tmp_path = None
    try:
        file_path = Path(target)
        tmp_path = file_path.with_name(file_path.name + ".tmp~")
        with tmp_path.open("w", encoding=encoding) as handle:
            handle.write(content)
        tmp_path.replace(file_path)  # 写完整了再替换，避免留下空文件
        return ""
    except (OSError, ValueError) as exc:
        # 清掉可能残留的临时文件，不给用户留垃圾
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
        return str(exc)


def _cell_capacities(cells, horizontal: bool) -> list:
    """
    【内部工具函数】判断每个单元格是否"吃得下更多空间"（自然尺寸模式用）。

    判断依据：该格子里的控件是不是按 expand=True 添加的（即会跟着格子一起变大）。
        有 expand=True 的控件 → 可以继续把富余空间分给这个格子；
        全是固定尺寸控件     → 格子不该为它膨胀，否则控件周围会空出一大片空白。
    参数：
        cells: 单元格列表（_BoxFrame）
        horizontal: True=横向分栏，看宽度方向
    返回：
        与 cells 等长的布尔列表
    """
    caps = []
    for cell in cells:
        if cell._has_expandable_child():
            caps.append(True)
            continue
        # 没有展开控件时，还可以看请求尺寸是否被外部撑大（例如嵌套的分栏容器）
        natural = cell._natural_size("w" if horizontal else "h")
        request = cell.winfo_reqwidth() if horizontal else cell.winfo_reqheight()
        caps.append(request - natural >= 2)
    return caps


def _split_one_axis(container: tk.Widget, cells, weights, horizontal: bool, gap: int,
                    proportional: bool, capacities=None):
    """
    【内部工具函数】算出各单元格在主轴（横向=宽 / 纵向=高）上应得的像素尺寸。

    返回的尺寸之和**严格等于容器主轴尺寸**，一个像素都不多、不少：
    容器空间被完全用满，中间不留空隙、边缘不留白边。

    两种模式的区别：
        严格比例（proportional=True）：完全按权重切分；取整丢掉的零头补给"最吃亏"
            的那一块，让每一块都最接近理论值（例如 790 像素高按 10:1 切，
            结果是 718:72 而不是 719:71）。
        非严格比例（proportional=False）：自然尺寸优先，并且只把富余空间分给
            capacities[i] 为 True 的格子（即内容 expand=True、还吃得下更多的格子）；
            更矮的格子保持自然尺寸，富余的像素留给排在后面的格子，
            不会在某个格子周围形成空白。

    参数：
        container: 分栏容器（HSplitFrame / VSplitFrame）
        cells: 单元格列表（_BoxFrame）
        weights: 各单元格权重，与 cells 一一对应
        horizontal: True=按宽度切分（左右分栏）；False=按高度切分（上下分栏）
        gap: 相邻单元格之间的间隙像素（0=无缝）
        proportional: True=严格按权重比例；False=自然尺寸优先
        capacities: 自然尺寸模式下各格子能否继续变大；None 表示按"全能变大"处理
    返回：
        各单元格的像素尺寸列表；容器尚未完成布局时返回 None
    """
    total = container.winfo_width() if horizontal else container.winfo_height()
    if total <= 1:
        return None  # 尚未完成布局，等下一次 Configure 再算
    # 间隙占用的空间先扣掉，剩下的全部切完
    usable = total - max(0, gap) * (len(cells) - 1)
    if usable < len(cells):
        return None  # 容器小到装不下任何内容，本次跳过，避免算出 0 或负数尺寸

    weight_sum = float(sum(weights))
    if weight_sum <= 0:
        ideals = [usable / float(len(cells))] * len(cells)  # 没设权重就平均分
    else:
        ideals = [usable * w / weight_sum for w in weights]
    sizes = [int(ideal) for ideal in ideals]  # 先向下取整

    axis_i = 0 if horizontal else 1
    # 各格子的"最小尺寸"：只由固定尺寸控件（expand=False 的按钮、文件选择框……）决定。
    # 可扩展控件（面板、分栏容器）本身能缩到任意大小，不给它设下限 ——
    # 否则它上报的尺寸会跟窗口一起变大，把权重带偏（设了 10:1 却分成一样高就是这么来的）。
    minimums = []
    for cell in cells:
        if cell._has_expandable_child():
            minimums.append(0)  # 有可扩展控件 → 可以缩小，不设下限
        else:
            minimums.append(max(1, cell._intrinsic_size(False)[axis_i]))

    if not proportional:
        intrinsic = minimums
        if capacities is None:
            capacities = [True] * len(cells)
        if sum(intrinsic) < usable:
            # 空间够放内容：先把固有尺寸分给每个格子，
            # 富余的部分只给"吃得下更多"的格子，按权重分
            extra = usable - sum(intrinsic)
            growable = [i for i, ok in enumerate(capacities) if ok]
            if weight_sum <= 0:
                shares = [extra // len(growable)] * len(growable) if growable else []
            else:
                grow_sum = float(sum(weights[i] for i in growable)) or 1.0
                shares = [int(extra * weights[i] / grow_sum) for i in growable]
            sizes = list(intrinsic)
            for i, share in zip(growable, shares):
                sizes[i] += share
            # 富余的取整零头，同样只补给能变大的格子
            rest = usable - sum(sizes)
            for i in growable:
                if rest <= 0:
                    break
                sizes[i] += 1
                rest -= 1
        elif sum(intrinsic) > 0:
            # 内容整体放不下：按固有尺寸等比压缩，保证每块都还看得见内容
            scale = usable / float(sum(intrinsic))
            sizes = [max(1, int(n * scale)) for n in intrinsic]
            overflow = sum(sizes) - usable
            if overflow > 0:
                sizes[-1] = max(1, sizes[-1] - overflow)
        # 若固有尺寸之和刚好等于可用空间，就直接用上面按权重算出的 sizes
        ideals = [float(s) for s in sizes]
    elif sum(minimums) < usable:
        # 比例模式：按权重切，但"装固定尺寸控件的格子"不会被切得比内容还小 ——
        # 这样只放按钮的格子就不会被按比例拉成一整格那么高。
        # 被补足的尺寸从其余格子按比例扣除，保证总和不变、比例尽量不动。
        too_small = [i for i in range(len(sizes)) if sizes[i] < minimums[i]]
        deficit = sum(minimums[i] - sizes[i] for i in too_small)
        donors = [i for i in range(len(sizes)) if i not in too_small]
        if donors and deficit > 0:
            pool = float(sum(sizes[i] for i in donors)) or 1.0
            for i in donors:
                sizes[i] -= int(deficit * sizes[i] / pool)
        for i in too_small:
            sizes[i] = minimums[i]
        # 取整误差修正：优先从还有富余的格子增减，保证总和精确等于可用空间
        while sum(sizes) != usable:
            need = usable - sum(sizes)
            step = 1 if need > 0 else -1
            donor = next((i for i in donors
                          if (sizes[i] - step) >= max(1, minimums[i])), None)
            if donor is None:
                break
            sizes[donor] += step
        ideals = [float(s) for s in sizes]

    # 比例模式下把取整丢掉的零头补给"最吃亏"的单元格：谁的小数部分大，谁就先补 1 像素。
    # 这样每一块都最接近理论大小（例如 790 按 10:1 切，得到 718:72，
    # 而不是把零头全丢给第一块的 719:71）。
    order = sorted(range(len(sizes)), key=lambda i: ideals[i] - sizes[i], reverse=True)
    for i in order:
        if sum(sizes) >= usable:
            break
        sizes[i] += 1
    # 兜底：总和精确对齐到可用空间，容器里不会剩下任何零散像素
    sizes[-1] = max(1, sizes[-1] + (usable - sum(sizes)))
    return sizes


def _layout_split(container: tk.Widget, cells, weights, horizontal: bool, gap: int,
                  proportional: bool):
    """
    【内部工具函数】把各单元格按算好的尺寸**精确摆进容器**。

    为什么用 place 而不用 grid：
        grid 会先满足控件的自然尺寸、再把剩余空间按 weight 分，权重只对"增量"生效；
        而 LogPanel 把自身请求尺寸钉成了当前像素尺寸，请求之和正好等于容器尺寸，
        grid 就认为没有剩余空间可分，于是一律按自然尺寸 1:1 排布 ——
        表现就是"设了 10:1，实际上下一样高"，格子外还会多出一圈空白。
        place 直接按像素坐标摆放，位置和尺寸完全由我们说了算：
        比例严格等于权重之比，且不留任何空隙。

    参数：同 _split_one_axis
    """
    # 自然尺寸模式下，只有"内容还吃得下更多空间"的格子才会被拉大
    capacities = None
    if not proportional:
        capacities = _cell_capacities(cells, horizontal)
    sizes = _split_one_axis(container, cells, weights, horizontal, gap, proportional,
                            capacities)
    if not sizes:
        return
    # 另一个方向：单元格铺满容器
    cross = container.winfo_height() if horizontal else container.winfo_width()
    if cross <= 0:
        return

    offset = 0
    for cell, size in zip(cells, sizes):
        size = max(1, size)
        if horizontal:
            cell.place(x=offset, y=0, width=size, height=cross)
        else:
            cell.place(x=0, y=offset, width=cross, height=size)
        offset += size + max(0, gap)


class _BoxFrame(tk.Frame):
    """
    【内部基础容器，用户不要直接实例化】
    HSplitFrame / VSplitFrame 的 left/right/top/bottom 都是该类型
    内置统一的add添加接口，实现所有容器API一致
    """
    def __init__(self, master):
        super().__init__(master)
        # 关闭尺寸传递：单元格的大小由分栏容器按比例指定，不允许内部控件反推，
        # 否则"内部控件按当前尺寸上报 → 单元格跟着变 → 比例被带偏"会形成循环
        self.pack_propagate(False)
        self.grid_propagate(False)
        # 已添加的子控件信息：(控件, 是否 expand, 控件真实需求尺寸)
        self._children_info = []

    def add(self, widget: tk.Widget, expand: bool = False):
        """
        向当前容器添加子控件

        :param widget: 子控件（LogPanel / FileSelect / MyButton / 其他分栏容器）
        :param expand: True=控件铺满本格子，随窗口缩放一起变大；
                       False（默认）=只占自身需要的大小，不被拉伸

        说明：
            expand=True 适合作编辑器 / 日志面板 / 嵌套分栏容器；
            expand=False（默认）适合按钮、文件选择框这类固定大小的控件：
                按自身尺寸摆放，并且格子也不会为它膨胀，
                所以严格比例分栏里，这样的控件不会被拉成一整格那么大。
        """
        filling = self._is_filling(widget, expand)
        widget.pack(fill=tk.BOTH if filling else tk.X, expand=filling)
        # 记住控件在"被铺满之前"的真实需求尺寸，作为格子的自然尺寸基准
        natural = self._child_natural(widget)
        self._children_info.append((widget, filling, natural))
        # 按当前内容刷新对外上报的请求尺寸与固有尺寸（分栏容器没被分配尺寸时也能撑开）
        self._report_natural_size()

    @staticmethod
    def _is_filling(widget: tk.Widget, expand: bool) -> bool:
        """
        【内部方法】判断某个子控件是否"会跟着格子一起变大"。

        规则：
            显式传了 expand=True → 会（铺满格子）；
            控件是本库的复合控件（类里带 _mytkui_composite 标记，例如 LogPanel、
                分栏容器、工具条、状态栏……）→ 会。
                这类控件天生就是用来占满可用空间的，即使调用时漏写 expand=True
                也按占满处理；
            其余原生控件（Button、Entry、Label……）→ 不会，按自身大小摆放。
        参数：
            widget: 子控件
            expand: 调用 add() 时传的 expand 参数
        返回：
            True 表示它会随格子一起变大
        """
        return bool(expand) or bool(getattr(widget, _COMPOSITE_ATTR, False))

    def _report_natural_size(self):
        """
        【内部方法】刷新本单元格对外上报的请求尺寸。

        为什么必须显式上报：
            单元格内部用 pack 摆放子控件，而 pack_propagate 已关闭，
            所以 Frame 自己不会把子控件的尺寸传上去。父容器（另一个分栏容器，
            甚至主窗口）正是通过 winfo_reqheight() 决定本单元格能拿多大，
            不上报的话它就只按 1×1 处理，整块区域会塌成一条线。

        上报口径与分栏模式对齐，避免两种模式互相打架：
            严格比例分栏：只上报固定尺寸控件的需求（expand=True 的控件反正会被铺满，
                上报它的尺寸会随窗口变大，把比例带偏）；
            自然尺寸分栏：上报全部内容的需求（面板才有一个合理的初始高度）。
        """
        if getattr(self.master, "proportional", False):
            width, height = self._intrinsic_size(False)
        else:
            width, height = self._natural_size("w"), self._natural_size("h")
        self.config(width=max(1, width), height=max(1, height))

    def measure_now(self, axis: str) -> int:
        """
        【内部方法】现场重新测量"装下当前内容需要多大"。

        和 _natural_size() 的区别：
            _natural_size() 用的是 add() 那一刻记下来的尺寸（刻意如此，
            为了不受后续窗口尺寸影响、避免布局漂移）；
            measure_now() 每次都会重新去问子控件，所以能感知"加进去之后
            内容又变了"的情况 —— AppShell 的顶部/底部这种按内容定高的区域需要它。
        参数：
            axis: "h" 量高度；其它值量宽度
        返回：
            像素尺寸，至少为 1
        """
        total = 0
        for child, _expanded, _recorded in self._children_info:
            size = self._child_natural(child)
            if size is None:
                continue
            if axis == "h":
                total += size[1]
            else:
                total = max(total, size[0])
        return max(1, total)

    def _natural_size(self, axis: str) -> int:
        """
        【内部方法】量出本单元格"装下内容需要多大"（记下来的真实需求尺寸）。

        为什么不用 winfo_reqheight() 现算：
            单元格的 pack_propagate 已关闭（防止内部控件把尺寸反推上来），
            而且 LogPanel 这类控件会把自身请求尺寸钉成当前分配到的尺寸，
            现算出来的值会随窗口尺寸变化。所以在 add() 时就记下每个控件的真实需求，
            之后一律用这份记录，布局结果就与调用时机无关、也不会来回漂移。
        参数：
            axis: "h" 量高度；其它值量宽度
        返回：
            自然尺寸（像素），至少为 1
        """
        return self._sum_children(axis, only_fixed=False)

    def _has_expandable_child(self) -> bool:
        """【内部方法】本格子里是否有按 expand=True 添加的控件（它会跟着格子一起变大）"""
        return any(expanded for _, expanded, _ in self._children_info)

    def _has_fixed_child(self) -> bool:
        """【内部方法】本格子里是否有按 expand=False 添加的固定尺寸控件"""
        return any(not expanded for _, expanded, _ in self._children_info)

    def _intrinsic_size(self, for_grow: bool = False):
        """
        【内部方法】量出内容的"固有尺寸"，供分栏容器决定这个格子给多大。

        基于 add() 时记下的控件真实需求尺寸，所以结果与窗口尺寸无关、不会漂移。

        参数：
            for_grow: True=优先用 expand=True 控件的需求尺寸（没有展开控件时退回固定控件）；
                      False=只算 expand=False 的控件，即"内容至少要占这么大"
        返回：
            (固有宽度, 固有高度) 二元组；没有对应控件时为 0
        """
        if for_grow and self._has_expandable_child():
            only_fixed = False
        else:
            only_fixed = True
        return (self._sum_children("w", only_fixed),
                self._sum_children("h", only_fixed))

    def _sum_children(self, axis: str, only_fixed: bool) -> int:
        """
        【内部方法】累加子控件的请求尺寸。

        参数：
            axis: "h" 累加高度；其它值取宽度的最大值
            only_fixed: True=只统计 expand=False 的控件（固有尺寸）；
                        False=统计全部控件（当前自然尺寸）
        返回：
            像素尺寸，至少为 1
        """
        total = 0
        for child, expanded, natural in self._children_info:
            if only_fixed and expanded:
                continue
            info = child.pack_info()  # 取 pack 的 pady/padx，保证量出来的尺寸和实际摆放一致
            pady = 2 * int(info.get("pady", 0))
            padx = 2 * int(info.get("padx", 0))
            if natural is None:
                natural = (1, 1)
            if axis == "h":
                total += natural[1] + pady
            else:
                total = max(total, natural[0] + padx)
        # 补上 Frame 自身边框占用的像素
        border = 2 * int(self.cget("bd") or 0)
        return max(1, total + border)

    def _child_natural(self, child: tk.Widget):
        """
        【内部方法】量出某个子控件"装下自己的内容需要多大"。

        为什么要临时打开尺寸传递、还要把父容器自身尺寸清零：
            1) 本单元格关掉了 pack_propagate（不让子控件反推格子大小），
               而 LogPanel、工具条这类复合控件自己也关掉了尺寸传递，
               直接读它们的 winfo_reqheight() 只会得到 1，量不出真实需求；
            2) 更关键的是：子控件的请求尺寸会被"父容器当前被钉成的尺寸"限制住。
               比如工具条已经被钉成 11 像素高，那么量它只会得到 11，
               哪怕它里面装的是 30 像素高的按钮 —— 于是再次重算时还是 11，
               工具条就被永久压成一条线。所以测量期间要把父容器自身
               尺寸清零（=不限制），量完立刻还原。
        参数：
            child: 子控件
        返回：
            (宽, 高)；量不出来时返回 None
        """
        cur_w = int(self.cget("width"))
        cur_h = int(self.cget("height"))
        try:
            self.config(width=0, height=0)      # 不限制，让子控件按内容上报
            child.pack_propagate(True)
            child.grid_propagate(True)
            # 先让 Tk 把"内容驱动"的请求尺寸算出来，再读；
            # 直接读会拿到切换前缓存的旧值
            self.update_idletasks()
            size = (child.winfo_reqwidth(), child.winfo_reqheight())
        except tk.TclError:
            return None
        finally:
            try:
                self.config(width=cur_w, height=cur_h)
                child.pack_propagate(False)
                child.grid_propagate(False)
            except tk.TclError:
                pass
        return size


class LogPanel(tk.Frame):
    """
    多行文本面板，可作为代码编辑器、日志输出控制台，也可当只读文本框用
    【功能】快捷键、Ctrl+滚轮字体缩放、按类别着色、字体/前景/背景色配置、只读锁定
    只读属性：
        read_only=False（默认）：正常可编辑
        read_only=True：只读，用户不能输入/删除/粘贴/剪切，
                        但依然能查看、鼠标选中、Ctrl+A 全选、Ctrl+C 复制、滚动
        构造时直接传：LogPanel(master, read_only=True)
        运行中切换：  panel.set_read_only(True) / panel.set_read_only(False)
        说明：只读只挡"用户的手"，程序自己仍然可以用 set_text / append /
              clear / info / error 更新内容（内部会自动临时解锁再锁上）。
    方法：
        info(msg) / warn(msg) / error(msg)：主线程按类别打印日志，自动滚动到底部
        safe_info(msg) / safe_warn(msg) / safe_error(msg)：子线程安全打印日志
        pstr(msg)：打印普通字符串，自动换行
        log(msg, color=None, prefix="")：打印一行并只给这一行指定颜色
        clear()：清空全部文本
        get_all_text()：获取面板全部文本
        get_selected_text()：获取鼠标选中的文本，无选中返回空字符串
        set_text(content)：覆盖写入文本（清空原有内容，填入新内容）
        insert_text(content) / append(text, color=None)：在末尾追加文本
        set_read_only(True/False)：切换用户可否编辑
        undo() / redo()：撤销 / 重做上一步编辑（等价于 Ctrl+Z / Ctrl+Y）
        clear_undo_history()：清空撤销历史（载入新内容后不想让用户撤回去时用）
    颜色与字体方法：
        set_font(font_name, font_size)：设置全局字体和字号
        set_zoom(step)：按步长缩放字号（正数放大，负数缩小）
        set_fg(color)：设置正文颜色，普通文本 / pstr / info 一起跟随它
        set_bg(color)：设置背景色，并自动换用适配的 warn/error 配色
        set_level_color(level, color)：单独指定某一类别颜色；color 传 None 恢复自动
        get_level_colors()：查看各类别当前的自动配色
        【重要】set_fg 只改"正文色"，不会把整屏日志染成同一个颜色：
        正文、info 跟随它一起变，warn/error 始终保持各自的醒目色。
        【常见误区】不要用 set_fg 来给某一条日志上色 ——
        那会改掉整个面板的正文色，之后写入的所有内容都会变成这个颜色。
        想临时强调某一行，请用 log(msg, color=...)。
    类别配色（LEVELS = info / warn / error / plain）：
        info / plain 跟随正文色（由 set_fg 决定）；
        warn / error 自动按背景明暗选色：浅色背景 warn=深黄 error=深红，
        深色背景 warn=亮黄 error=亮红，保证深色主题下也看得清。
        想固定某类别颜色用 set_level_color，例如：
            panel.set_level_color("error", "#FF3B30")
    快捷键（面板激活时生效）
        Ctrl+A 全选文本
        Ctrl+C 复制选中
        Ctrl+X 剪切选中（只读时不生效）
        Ctrl+V 粘贴（只读时不生效）
        Ctrl+Z 撤销上一步编辑（只读时不生效）
        Ctrl+Y 重做（只读时不生效）
        Ctrl+S 触发 on_save 回调（需要自己绑定逻辑）
        Ctrl+鼠标滚轮 ↑：放大字体；↓：缩小字体【仅改字号，保留视口，布局不抖动】
    属性：
        .native_widget：底层原生 ScrolledText 对象，用于高级自定义
        .on_save：Ctrl+S触发的回调函数
        .read_only：是否只读（True/False，可直接改，也可以用 set_read_only）
    行号（默认打开）：
        构造时 show_line_numbers=False 可关闭；也可以随时 panel.set_line_numbers(False) 切换
        行号画在左侧的 .gutter 画布上，随文本滚动自动跟随，增删行自动重排
        set_font / set_zoom 缩放字号后行号会重新对齐（行高变化也能对上）
    语法高亮（对特定文本自动换色）：
        add_highlight(pattern, color=..., background=..., bold=..., italic=...,
                      underline=..., name=..., override_level=True)
            pattern: 正则表达式字符串或已编译的正则；color=None 表示不改颜色
            例：panel.add_highlight(r"\b(HLT|NOP)\b", color="#FF6B6B", bold=True)
        remove_highlight(name)：按名字删掉一条规则
        clear_highlights()：清掉全部高亮规则
        refresh_highlights()：按当前规则重新着色（规则改过可手动调，一般不用调）
        【重要】高亮默认覆盖类别颜色（override_level=True），所以日志面板里
        也能用高亮把某段文字染成别的颜色；文本改动后面板会自动重新着色。
    """
    # 复合控件标记：被 add() 添加时自动铺满所在格子（见 _is_filling）
    _mytkui_composite = True
    # 字号允许范围（构造、缩放、set_font 都受此限制），防止字号失控
    MIN_FONT_SIZE = 8
    MAX_FONT_SIZE = 40
    # 文本类别标签（Text 的 tag 名），用来给不同类别的内容上不同颜色
    LEVELS = ("info", "warn", "error", "plain")
    # 两套预设配色：浅色背景用 False 那套，深色背景用 True 那套。
    # 只描述"类别配色"，正文颜色由 set_fg 决定。
    _PALETTES = {
        False: {  # 浅色背景（例如白底）
            "warn": "#A15C00",
            "error": "#C00000",
        },
        True: {  # 深色背景（例如 #222222）
            "warn": "#E8C547",
            "error": "#FF6B6B",
        },
    }

    def __init__(self, master, font_name="Consolas", font_size=11, fg="black",
                 bg="white", read_only: bool = False,
                 show_line_numbers: bool = True,
                 line_number_color: Optional[str] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.root = self.winfo_toplevel()
        self.on_save: Optional[Callable[[], None]] = None  # Ctrl+S保存回调
        # 是否只读：True 时用户只能查看、选中、复制，改不动内容
        self.read_only = bool(read_only)

        # 字体配置
        font_size = max(self.MIN_FONT_SIZE, min(self.MAX_FONT_SIZE, int(font_size)))
        self.font_name = font_name
        self.font_size = font_size
        self.font = tkFont.Font(family=self.font_name, size=self.font_size)

        # 已经钉定的面板像素尺寸（0 表示尚未钉定）
        self._pin_w = 0
        self._pin_h = 0

        # ========== 行号与语法高亮状态 ==========
        self._show_line_numbers = bool(show_line_numbers)
        # 行号颜色默认按背景明暗自动选：浅底用灰、深底用浅灰，保证看得清
        self._line_number_color = line_number_color or ("#8A8A8A" if self._is_dark(bg) else "#9A9A9A")
        self._gutter_bg = bg
        self._gutter_width = 0
        self._gutter_font_cache = None
        self._gutter_digit_width = None
        # 高亮规则：[(规则名, 正则, 样式字典, 是否覆盖类别颜色)]
        self._highlights = []
        # 上一次已知的内容，用来判断"文本是否变了"（比 edit_modified 可靠，见 _watch_text）
        self._last_content = None
        self._watch_job = None
        self._redraw_job = None
        self._highlight_job = None
        # 待重算的起始行（末尾追加场景用，见 _after_content_change）
        self._dirty_from_row = None
        # "滚动到最后一行"的合并任务
        self._see_job = None
        # 上一轮巡检时的长度/行数，以及上次高亮扫描的起点与当时的长度
        self._last_length = None
        self._last_rows = None
        self._scanned_from_row = None
        self._scanned_length = None

        # undo=True 打开 Text 自带的撤销栈，Ctrl+Z / Ctrl+Y 才能撤销/重做。
        # 分隔符沿用 Tk 默认（autoseparators=True）：连续输入算一次撤销，
        # 关闭一次撤销范围由 Tk 自动按"操作时间/内容变化"划分
        self.text = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=self.font,
                                             fg=fg, bg=bg, undo=True)
        # 行号槽画在左侧 Canvas 上（不是另一个 Text 控件，省内存、也不用同步滚动条）
        self.gutter = tk.Canvas(self, highlightthickness=0, borderwidth=0, bg=bg,
                                width=self._gutter_width)
        # 行号槽固定在最左列、宽度按需自适应；文本框铺满剩余空间
        self.gutter.grid(row=0, column=0, sticky="ns")
        self.text.grid(row=0, column=1, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        if not self._show_line_numbers:
            self.gutter.grid_remove()   # 构造时就要求关掉行号

        # ========== 类别配色 ==========
        self._bg_color = bg
        self._fg_color = fg
        self._level_colors = {}
        # 用户用 set_level_color 手动指定的类别颜色（换背景色时不会被覆盖）
        self._manual_levels = {}
        # insert_line(..., color=...) 用的临时颜色标签序号，保证带色文本有独立标签
        self._custom_tag_seq = 0
        self._apply_palette()

        # ========== 关键：阻止字号变化影响父容器布局 ==========
        # 第1层（内）：文本框自身的请求尺寸不随字号膨胀
        self.text.bind("<Configure>", self._on_text_configure)
        # 第2层（外）：面板对外上报的尺寸精确等于当前像素尺寸，
        #             分栏比例在缩放时才能做到一个像素都不动
        self.bind("<Configure>", self._on_panel_configure)

        # ========== 滚动 / 尺寸联动 ==========
        # 文本框滚动时重画行号。yscrollcommand 是控件的回调选项（不是可 bind 的事件），
        # ScrolledText 已经把它接到滚动条上了，所以这里要"链"上去：先转交原来的，
        # 再画自己的，否则会把滚动条的回调顶掉、滚动条就失效了。
        old_yscroll = self.text.cget("yscrollcommand")

        def _on_yscroll(first, last):
            if old_yscroll:
                self.text.tk.call(old_yscroll, first, last)
            self._on_text_yscroll()

        self.text.config(yscrollcommand=_on_yscroll)
        self._yscroll_callback = _on_yscroll  # 存一份引用，防止被回收
        # 鼠标停在行号槽上也能滚
        self.gutter.bind("<MouseWheel>", self._on_gutter_wheel)
        # 面板销毁时撤掉后台巡检，避免窗口关掉后还去访问已销毁的控件
        self.bind("<Destroy>", self._on_destroy)
        # 首帧之后开始盯着内容变化
        self.after_idle(self._watch_text)

        # ========== 绑定快捷键 ==========
        self.text.bind("<Control-a>", self._hotkey_select_all)
        self.text.bind("<Control-c>", self._hotkey_copy)
        self.text.bind("<Control-x>", self._hotkey_cut)
        self.text.bind("<Control-v>", self._hotkey_paste)
        self.text.bind("<Control-s>", self._hotkey_save)
        # 撤销 / 重做：Text 自带撤销栈（构造时 undo=True 开启）
        self.text.bind("<Control-z>", self._hotkey_undo)
        self.text.bind("<Control-y>", self._hotkey_redo)
        # Ctrl+鼠标滚轮缩放字体
        self.text.bind("<Control-MouseWheel>", self._mousewheel_zoom)

        # 只读面板最后才锁上：上面的配色和内容写入都需要控件处于可写状态
        if self.read_only:
            self.text.config(state="disabled")

    # ---------------- 字体颜色API ----------------
    def set_font(self, font_name: str, font_size: int):
        """
        设置面板全局字体名称和字号（不会撑坏父容器布局）。

        字号变了行高也变，所以行号字体与位置会一起重新对齐。
        """
        font_size = int(font_size)
        font_size = max(self.MIN_FONT_SIZE, min(self.MAX_FONT_SIZE, font_size))
        self.font.config(family=font_name, size=font_size)
        self.font_name = font_name
        self.font_size = font_size
        # 行号字体跟着正文走，缓存作废后重新生成
        self._gutter_font_cache = None
        self._gutter_digit_width = None
        self._gutter_width = 0
        # 换字体/字号后立即重钉请求尺寸，避免布局被撑变形
        self._pin_requested_size()
        self.refresh_highlights()          # 高亮里带粗体/斜体，字体变了要重算
        self._sync_modified_tracking()     # 行高变了，行号要重画

    def set_fg(self, color: str):
        """
        设置正文颜色，支持颜色名/十六进制 #RRGGBB。

        正文色同时作用于：普通文本、附加文本、info（这几个类别跟随正文色，
        不单独打颜色标签）。因为走的是 Text 的默认前景色，
        所以已写好的普通文本与 info 会一起变成新颜色，
        而 warn / error 的醒目色和用户手动指定的颜色不受影响。
        """
        self._fg_color = color
        self.text.config(fg=color)

    def set_bg(self, color: str):
        """
        设置背景色，支持颜色名/十六进制 #RRGGBB。

        同时会按新背景的明暗自动换用合适的警告/错误配色（深色背景用亮黄亮红，
        浅色背景用深黄深红），保证在深色主题下内容依然看得清。
        已经被 set_level_color 手动指定过的类别不会被覆盖。
        """
        self._bg_color = color
        self.text.config(bg=color)
        # 行号槽背景与文本区保持一致，看上去是一整块
        self._gutter_bg = color
        self.gutter.config(bg=color)
        self._apply_palette()  # 只覆盖没被用户手动指定过的类别
        self._schedule_gutter_redraw()

    def set_level_color(self, level: str, color: Optional[str]):
        """
        设置某一类别文本的颜色。

        参数：
            level: "info" / "warn" / "error" / "plain"
            color: 颜色名或 #RRGGBB；传 None 表示恢复成自动配色
        示例：
            panel.set_level_color("error", "#FF3B30")   # 错误用亮红
            panel.set_level_color("info", None)         # 恢复自动配色
        """
        if level not in self.LEVELS:
            raise ValueError(f"类别名必须是 {self.LEVELS} 之一，收到 {level!r}")
        if color is None:
            self._manual_levels.pop(level, None)  # 撤销手动指定，回到自动配色
        else:
            self._manual_levels[level] = color
        self._apply_palette()

    def get_level_colors(self) -> dict:
        """返回当前各类别各自的颜色，便于调试或做主题切换"""
        return dict(self._level_colors)

    def _is_dark(self, color: str) -> bool:
        """
        【内部方法】判断给定颜色是深色还是浅色（决定用哪套配色）。
        做法：取 #RRGGBB 三通道按人眼敏感度加权求亮度，亮度低于中值算深色。
        参数：
            color: 颜色名或 #RRGGBB
        返回：
            True 表示深色
        """
        try:
            r, g, b = self.winfo_rgb(color)  # 拿到 0~65535 的三通道
            r, g, b = r >> 8, g >> 8, b >> 8
            return (0.299 * r + 0.587 * g + 0.114 * b) < 128
        except tk.TclError:
            return False  # 认不出来的颜色名按浅色处理

    def _apply_palette(self):
        """
        【内部方法】按当前背景明暗铺一套配色。

        只有 warn / error 需要独立颜色（醒目提示用），info / plain 记为 None ——
        表示"用面板的正文色"，也就是不单独打颜色标签，直接跟随 Text 的默认前景色。
        这样 set_fg 改正文色时，正文与 info 会一起变，而 warn/error 保持自己的颜色，
        已写好的内容也不会被整屏染成同一个色。
        用户用 set_level_color 手动指定过的类别，始终优先。
        """
        palette = self._PALETTES[self._is_dark(self._bg_color)]
        colors = {
            "info": None,   # None = 跟随正文色（set_fg）
            "plain": None,
            "warn": palette["warn"],
            "error": palette["error"],
        }
        colors.update(self._manual_levels)  # 用户指定过的覆盖预设
        self._level_colors = colors
        self._refresh_level_tags()

    def _refresh_level_tags(self):
        """
        【内部方法】把当前配色应用到 Text 的各个标签上。

        颜色为 None 的类别（默认的 info / plain）不打颜色标签，
        直接跟随 Text 的默认前景色（即 set_fg 设的正文色）。
        这一点很关键：如果给它们打上固定的颜色标签，之后 set_fg 改正文色时，
        已经写好的内容会被标签颜色"锁住"或被整屏重染，两种都不符合预期。
        """
        for level in self.LEVELS:
            color = self._level_colors.get(level)
            if color is None:
                # 清掉之前可能设过的颜色，让它回到跟随正文色
                self.text.tag_config(level, foreground="")
            else:
                self.text.tag_config(level, foreground=color)
        # 类别标签改动后，重新把高亮标签抬到它们上面，保证高亮颜色生效
        self._restore_highlight_priority()

    def _restore_highlight_priority(self):
        """
        【内部方法】按规则设置高亮标签相对类别标签的优先级。

        为什么需要它：Tk 里同一个字符被多个标签覆盖时，**后创建的标签优先**。
        而类别标签会随着 set_fg / set_bg / set_level_color 反复重新配置，
        每次重配都会把它自己抬到最上面 —— 所以每改一次配色都要重排一次：
            规则 override_level=True  → 高亮抬到类别标签之上，颜色说了算；
            规则 override_level=False → 高亮降到类别标签之下，保住日志本身的颜色。
        """
        for rule_name, _, _, override in self._highlights:
            try:
                if override:
                    self.text.tag_raise(rule_name)
                else:
                    self.text.tag_lower(rule_name)
            except tk.TclError:
                pass

    # ---------------- 行号 ----------------
    def set_line_numbers(self, show: bool = True):
        """
        打开 / 关闭行号显示。
        参数：
            show: True=显示行号（默认就是打开的），False=隐藏
        """
        self._show_line_numbers = bool(show)
        if self._show_line_numbers:
            self.gutter.grid()
            self._schedule_gutter_redraw()
        else:
            self.gutter.grid_remove()

    def _gutter_font(self) -> tkFont.Font:
        """
        【内部方法】行号用的字体：与正文同字体、字号略小一点。

        行高必须与正文一致，否则行号会和文本行错位，所以只把字号调小一号
        （Tk 的字体对象是跨控件共享的，必须单独建一个，不能直接改正文那个）。
        """
        size = max(self.MIN_FONT_SIZE - 2, min(self.MAX_FONT_SIZE, self.font_size - 1))
        return tkFont.Font(family=self.font_name, size=size)

    def _on_text_yscroll(self, *args):
        """【内部方法】文本框滚动回调：行号跟着一起滚（内部方法，勿手动调用）"""
        if self._show_line_numbers:
            self._schedule_gutter_redraw()

    def _on_gutter_wheel(self, event):
        """鼠标停在行号槽上滚动时，把滚动转给文本框"""
        self.text.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"

    def _schedule_gutter_redraw(self):
        """
        【内部方法】把行号重画合并成"至多每 40 毫秒一次"。

        为什么不用 after_idle：连续写日志时每次插入都会触发滚动、
        进而触发一次行号重画，after_idle 等于每行都重画（行数一多就很浪费）。
        用一个小延时合并之后，滚动的观感不变，但重画次数与"写入次数"脱钩。
        """
        if self._redraw_job is not None:
            return
        try:
            self._redraw_job = self.after(40, self._draw_line_numbers)
        except tk.TclError:
            self._redraw_job = None

    def _draw_line_numbers(self):
        """
        【内部方法】重画行号槽。

        只画当前可见的那几行（用文本行高算出首尾行号），所以文本再长也只画几十个数字。
        """
        self._redraw_job = None
        if not self._show_line_numbers:
            return
        try:
            self.gutter.delete("all")
            if not self.text.winfo_ismapped():
                return
            index = self.text.index("@0,0")          # 当前可见的第一行，形如 "12.0"
            first_row = int(index.split(".")[0])
            height = self.text.winfo_height()
            line_height = max(1, self.font.metrics("linespace"))
            rows = height // line_height + 2
            total_rows = int(self.text.index("end-1c").split(".")[0])
            for row in range(first_row, first_row + rows):
                if row > total_rows:
                    break
                bbox = self.text.bbox(f"{row}.0")
                if bbox is None:                     # 该行还没完成布局，跳过
                    continue
                _, y, _, h = bbox
                self.gutter.create_text(self._gutter_width - 4, y + h // 2,
                                        anchor="e", text=str(row),
                                        fill=self._line_number_color,
                                        font=self._line_number_font())
        except tk.TclError:
            pass  # 面板正在销毁，忽略

    def _line_number_font(self):
        """【内部方法】行号字体（缓存起来，避免每帧都新建字体对象）"""
        if getattr(self, "_gutter_font_cache", None) is None:
            self._gutter_font_cache = self._gutter_font()
        return self._gutter_font_cache

    def _update_gutter_width(self):
        """
        【内部方法】按行数调整行号槽宽度。

        宽度用"最宽的那个行号"算出来，位数从 9 变到 10 时自动加宽，不会截断。
        数字宽度按 10 个字符量一次并缓存：每写一行都调 font.measure() 的话，
        会白白多出几万个 Tcl 调用（实测写日志每行要多花约 1 毫秒）。
        """
        total_rows = max(1, int(self.text.index("end-1c").split(".")[0]))
        digits = len(str(total_rows))
        if self._gutter_digit_width is None:
            font = self._line_number_font()
            # 取 0~9 里最宽的一个，保证任何行号都放得下
            self._gutter_digit_width = max(font.measure(str(d)) for d in range(10))
        width = self._gutter_digit_width * digits + 10
        if width != self._gutter_width:
            self._gutter_width = width
            self.gutter.config(width=width)

    # ---------------- 语法高亮 ----------------
    def add_highlight(self, pattern, color: Optional[str] = None,
                      background: Optional[str] = None,
                      bold: bool = False, italic: bool = False,
                      underline: bool = False, name: Optional[str] = None,
                      override_level: bool = True) -> str:
        """
        添加一条语法高亮规则：对匹配 pattern 的文本自动换色。

        参数：
            pattern: 正则表达式（字符串或已 re.compile 的对象），按整篇文本匹配
            color: 文字颜色，支持颜色名或 #RRGGBB；None 表示不改文字颜色
            background: 背景颜色；None 表示不改背景
            bold / italic / underline: 是否加粗 / 倾斜 / 下划线
            name: 规则名，便于以后 remove_highlight(name) 删除；
                  不传则自动用 "hl_序号"
            override_level: True（默认）表示这条规则的颜色**覆盖**日志类别颜色，
                            可以把某段文字强行染成指定颜色；
                            False 表示只在没有类别色的地方生效
        返回：
            规则名（可用于 remove_highlight）
        示例：
            panel.add_highlight(r"\\b(HLT|NOP)\\b", color="#FF6B6B", bold=True)
            panel.add_highlight(r"@\\w+", color="#4EC9B0")          # 跳转标签用青色
            panel.add_highlight(r"R[0-6]\\b", color="#DCDCAA")      # 寄存器用浅黄
        """
        rule_name = name or f"hl_{len(self._highlights)}"
        if isinstance(pattern, str):
            regex = re.compile(pattern)
        else:
            regex = pattern
        style = {"foreground": color, "background": background,
                 "bold": bool(bold), "italic": bool(italic),
                 "underline": bool(underline)}
        self._highlights = [h for h in self._highlights if h[0] != rule_name]
        self._highlights.append((rule_name, regex, style, bool(override_level)))
        self._refresh_highlight_tag(rule_name, style)
        self.refresh_highlights()
        return rule_name

    def remove_highlight(self, name: str):
        """删掉一条高亮规则（规则不存在也不会报错）"""
        self._highlights = [h for h in self._highlights if h[0] != name]
        try:
            self.text.tag_delete(name)
        except tk.TclError:
            pass
        self.refresh_highlights()

    def clear_highlights(self):
        """清掉全部高亮规则（不影响日志类别颜色）"""
        for rule_name, _, _, _ in self._highlights:
            try:
                self.text.tag_delete(rule_name)
            except tk.TclError:
                pass
        self._highlights = []
        self.refresh_highlights()

    def get_highlights(self) -> list:
        """查看当前所有高亮规则名，便于调试"""
        return [rule_name for rule_name, _, _, _ in self._highlights]

    def refresh_highlights(self, from_index: str = "1.0", to_index: Optional[str] = None):
        """
        按当前规则给文本重新着色。

        参数：
            from_index: 从哪一行开始重算，默认 "1.0"（整篇）。
                        写日志这种"只在末尾追加"的场景会自动只算新增的部分。
            to_index: 只重算到哪一行（默认算到末尾）。
        说明：
            一般不用手动调用：写入内容后面板会自动重着色。
        """
        # 清掉要重算那一段上的旧高亮。
        # 注意 to_index 一定要给：tag_remove(tag, from, "end") 会一直扫到文章末尾，
        # 在"每写一行都重算"的场景里就是 O(n) 一次、总代价 O(n²)。
        end_of_scope = to_index if to_index is not None else tk.END
        try:
            for rule_name, _, _, _ in self._highlights:
                self.text.tag_remove(rule_name, from_index, end_of_scope)
        except tk.TclError:
            return

        no_rules = not self._highlights
        for rule_name, regex, style, override in self._highlights:
            for start, end in self._iter_matches(regex, from_index, to_index):
                try:
                    self.text.tag_add(rule_name, start, end)
                except tk.TclError:
                    return
        # 全部打完之后统一排一次优先级（Tk 的标签优先级由 tag_raise/tag_lower 决定）
        self._restore_highlight_priority()
        # 记下"这次扫到哪儿了"，供下一次巡检判断能否只算新增部分
        try:
            self._scanned_from_row = int(str(from_index).split(".")[0])
            self._scanned_length = self._index_to_length(self.text.index("end-1c"))
        except tk.TclError:
            self._scanned_from_row = None
            self._scanned_length = None
        if not no_rules:
            self._sync_modified_tracking()

    def _refresh_highlight_tag(self, rule_name: str, style: dict):
        """【内部方法】把样式写进标签；颜色为 None 的项不设置，避免把原有颜色顶掉"""
        options = {}
        if style.get("foreground") is not None:
            options["foreground"] = style["foreground"]
        if style.get("background") is not None:
            options["background"] = style["background"]
        font = tkFont.Font(font=self.text.cget("font"))
        if style.get("bold"):
            font.config(weight="bold")
        if style.get("italic"):
            font.config(slant="italic")
        if style.get("underline"):
            font.config(underline=True)
        if any(style.get(k) for k in ("bold", "italic", "underline")):
            options["font"] = font
        self.text.tag_config(rule_name, **options)

    def _iter_matches(self, regex, from_index: str = "1.0", to_index: Optional[str] = None):
        """
        【内部方法】遍历文本里所有匹配位置（默认从第 1 行扫到最后）。

        逐行匹配：正则不会跨行吞掉换行，也不会因为多行模式意外匹配到别的行。
        参数：
            regex: 已编译的正则
            from_index: 起始位置，例如 "12.0" 表示从第 12 行开始扫
            to_index: 结束位置；给了就只扫到那一行为止（增量重算用）
        """
        try:
            total_rows = int(self.text.index("end-1c").split(".")[0])
            first_row = max(1, int(str(from_index).split(".")[0]))
            if to_index is not None:
                total_rows = min(total_rows, int(str(to_index).split(".")[0]))
        except tk.TclError:
            return  # 面板正在销毁
        for row in range(first_row, total_rows + 1):
            try:
                line = self.text.get(f"{row}.0", f"{row}.end")
            except tk.TclError:
                return
            for match in regex.finditer(line):
                if match.start() == match.end():
                    continue
                yield (f"{row}.{match.start()}", f"{row}.{match.end()}")

    # ---------------- 内容变化监听 ----------------
    def _on_destroy(self, event=None):
        """【内部方法】面板被销毁时撤掉后台巡检任务，避免访问已销毁的控件"""
        for job in (self._watch_job, self._redraw_job, self._highlight_job, self._see_job):
            if job is not None:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
        self._watch_job = None
        self._redraw_job = None
        self._highlight_job = None
        self._see_job = None

    def _watch_text(self):
        """
        【内部方法】定期检查文本有没有变化（Tk 没有"内容变了"事件，只能这样查）。

        为什么不用 edit_modified()：它记的是"相对于上次复位有没有改动"，
        撤销回到旧内容后会被 Tk 复位成 False，于是漏掉变化、行号和高亮就不刷新了。

        为了不白白扫大文件，先比"长度 + 行数"这两个廉价指标：
        都没变就直接跳过（绝大多数轮询走这条路，几乎不花时间）；
        只有变了才读全文确认，并且只重算"上一次扫码起点之后"的部分。
        """
        self._watch_job = None
        try:
            end_index = self.text.index("end-1c")
            rows = int(end_index.split(".")[0])
            length = self._index_to_length(end_index)
        except tk.TclError:
            return  # 面板已销毁，不再继续

        if (length, rows) != (self._last_length, self._last_rows):
            # 长度或行数变了：确认一下内容（写入方会把 _last_content 置空要求重读）
            if self._last_content is None:
                try:
                    self._last_content = self.text.get("1.0", "end-1c")
                except tk.TclError:
                    return
            self._sync_modified_tracking()
            # 只变了末尾（纯追加）就从上次扫过的位置继续，否则老实整篇重算
            if (self._scanned_length is not None
                    and length >= self._scanned_length
                    and self._scanned_from_row):
                self.refresh_highlights(f"{self._scanned_from_row}.0")
            else:
                self._schedule_highlight_refresh()

        self._last_length, self._last_rows = length, rows
        # 每 200 毫秒查一次，足够跟手，也不会占 CPU
        try:
            self._watch_job = self.after(200, self._watch_text)
        except tk.TclError:
            self._watch_job = None

    def _sync_modified_tracking(self):
        """【内部方法】内容或行数变化后：更新行号槽宽度并重画行号"""
        if not self._show_line_numbers:
            return
        self._update_gutter_width()
        self._schedule_gutter_redraw()

    def _after_content_change(self, appended_from_row: Optional[int] = None):
        """
        【内部方法】写完内容后的统一收尾：刷新内容记录 + 行号 + 语法高亮。

        参数：
            appended_from_row: 如果这次只是"在末尾追加"，传新增内容的第一行行号，
                               高亮就只重算从这里开始的部分，不必整篇重扫。
                               连续写日志时这样处理，开销与已写行数无关。

        为什么高亮要合并到空闲时算：整篇重扫是 O(n)，
        每写一行都扫一次就退化成 O(n²)（实测 550 行会耗时 60 秒）。
        """
        try:
            # 只更新"廉价指标"（行数、总字符数），不读全文：
            # 每写一行都 get('1.0','end') 读一遍是 O(n)，同样会退化成 O(n²)。
            # 全文比对留给 _watch_text 的定时巡检去做，那里本来就要读一次。
            end_index = self.text.index("end-1c")
            self._last_rows = int(end_index.split(".")[0])
            self._last_length = self._index_to_length(end_index)
            self._last_content = None   # 内容已变，让巡检下次读全文重新确认
        except tk.TclError:
            return
        self._sync_modified_tracking()
        if not self._highlights:
            return
        if appended_from_row is not None:
            # 只在末尾追加：立刻（但只）处理新增的那几行，日志场景下这是 O(1)
            self.refresh_highlights(f"{appended_from_row}.0")
        else:
            self._schedule_highlight_refresh()

    def _index_to_length(self, index: str) -> int:
        """
        【内部方法】用 Tk 自己的计数算出"到 index 为止有多少个字符"。

        等价于 len(text.get("1.0", index))，但完全在 Tcl 侧统计，不把正文读进 Python。
        只用来判断"长度有没有变化"，所以只要前后口径一致就行。
        """
        try:
            counted = self.text.count("1.0", index, "chars")
        except tk.TclError:
            return -1
        return int(counted[0]) if counted else 0

    def _schedule_highlight_refresh(self):
        """【内部方法】把整篇高亮重算推迟到空闲时（多次写入只会算一次）"""
        if not self._highlights or self._highlight_job is not None:
            return
        try:
            self._highlight_job = self.after_idle(self._run_highlight_refresh)
        except tk.TclError:
            self._highlight_job = None

    def _run_highlight_refresh(self):
        """【内部方法】真正执行一次整篇高亮重算"""
        self._highlight_job = None
        self.refresh_highlights()

    def insert_line(self, text: str, level: str = "plain", color: Optional[str] = None):
        """
        在末尾追加一段文本，并给它单独上色（其余内容不受影响）。

        参数：
            text: 要写入的文本
            level: 类别，LEVELS 之一；决定用哪套自动配色
            color: 直接指定颜色（优先于 level 的自动配色）；None 表示按 level 走
        说明：
            这是"临时强调某一段"的正确做法 —— 不用 set_fg 改整个面板的颜色，
            那样之后写入的所有内容都会跟着变。
        """
        start = self.text.index("end-1c")  # 注意不是 END：END 之后的位置取不到内容
        start_row = int(str(start).split(".")[0])
        old_state = self._writable_state()
        self.text.insert(tk.END, text)
        if color is not None:
            # 一次性标签：只覆盖这一段，不影响已写好的内容和后面的内容
            tag = f"custom_{self._custom_tag_seq}"
            self._custom_tag_seq += 1
            self.text.tag_config(tag, foreground=color)
            self.text.tag_add(tag, start, "end-1c")
        elif self._level_colors.get(level) is not None:
            self.text.tag_add(level, start, "end-1c")
        self.text.see(tk.END)      # 滚到最新一行。
        # 这里必须"立刻"滚：see() 让 Tk 只对可见区域做排版，一旦推迟，
        # 排版范围会扩散到整篇文本，连续写入反而从线性退化成平方级。
        self._restore_state(old_state)
        # 内容变了：行号与语法高亮跟着更新；这是末尾追加，所以高亮只算新增部分
        self._after_content_change(appended_from_row=start_row)

    def _schedule_see_end(self):
        """
        【内部方法】把"滚动到最后一行"合并到空闲时做一次。

        连续写日志时如果每行都 see(END)，会触发 N 次滚动、N 次行号重画
        （实测这部分占了写日志总耗时的一大半），合并之后只做一次。
        """
        if self._see_job is not None:
            return
        try:
            self._see_job = self.after_idle(self._run_see_end)
        except tk.TclError:
            self._see_job = None

    def _run_see_end(self):
        """【内部方法】真正把视图滚到最后一行"""
        self._see_job = None
        try:
            self.text.see(tk.END)
        except tk.TclError:
            pass

    def append(self, text: str, color: Optional[str] = None):
        """
        在末尾追加文本（不额外加换行），可指定颜色。
        参数：
            text: 要追加的文本
            color: 颜色名或 #RRGGBB；None 表示用正文色
        """
        self.insert_line(text, level="plain", color=color)

    def clear(self):
        """
        清空面板内全部文本。

        清空之后撤销历史会重置（清空结果作为新的起点），
        所以之后按 Ctrl+Z 撤销的是清空之后新写入的内容，不会把面板还原成清空前
        那一大堆旧文本 —— 这是编辑器的通行做法（载入/清空等整体操作不留撤销点）。
        如果确实需要"清空前的内容"能撤回来，请在清空前自己备份
        （get_all_text() 存一份）。
        """
        old_state = self._writable_state()
        self.text.delete("1.0", tk.END)
        self._restore_state(old_state)
        self._reset_undo_baseline()
        self._after_content_change()

    def set_text(self, content: str):
        """
        覆盖式写入文本：清空原有内容，填入新文本，自动滚动到末尾。

        写入的内容跟随正文色（set_fg 设的颜色），不会被打上类别标签。
        与 clear 一样，写入后撤销历史会重置：这次写入的内容成为新起点，
        之后按 Ctrl+Z 撤销的是"写完之后又新写的内容"，
        不会把面板倒回上一份文件内容（导入新文件后不该还能撤回到旧文件）。
        需要保留旧内容时请自己先 get_all_text() 备份。
        """
        old_state = self._writable_state()
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, content)
        self.text.see(tk.END)
        self.text.update_idletasks()
        self._restore_state(old_state)
        self._reset_undo_baseline()
        self._after_content_change()

    def get_all_text(self, strip_last_newline: bool = True) -> str:
        """
        获取全部文本。
        参数：
            strip_last_newline: True（默认）=剔除末尾多余换行，方便直接拿去用；
                                False=原样返回（写回文件等场景更合适）
        返回：
            面板全部文本字符串
        """
        content = self.text.get("1.0", tk.END)
        return content.rstrip("\n") if strip_last_newline else content

    def get_selected_text(self) -> str:
        """获取鼠标选中的文本，未选中返回空串"""
        try:
            return self.text.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            return ""

    # ---------------- 快捷键事件处理 ----------------
    def _hotkey_select_all(self, event):
        self.text.tag_add(tk.SEL, "1.0", tk.END)
        self.text.mark_set(tk.INSERT, "1.0")
        return "break"

    def _hotkey_copy(self, event):
        self.text.event_generate("<<Copy>>")
        return "break"

    def _hotkey_undo(self, event):
        """
        Ctrl+Z 撤销上一步编辑。

        撤销的是零散编辑：用户自己敲进去的字、按类别打印的每一行日志、
        append / append_line 追加的内容，一次 Ctrl+Z 撤掉一步。
        整体写入（set_text / clear）不留撤销点，它们是新的起点，见这两个方法的说明。
        只读面板直接忽略（用户本来就不能改，没有需要撤销的内容）；
        撤销栈为空时什么都不做，也不会弹出 tkinter 报错。
        """
        if self.read_only:
            return "break"
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass  # 撤销栈为空，忽略即可
        return "break"

    def _hotkey_redo(self, event):
        """Ctrl+Y 重做（把刚撤销掉的编辑重新做回来）"""
        if self.read_only:
            return "break"
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass  # 没有可重做的内容，忽略
        return "break"

    def _reset_undo_baseline(self):
        """
        【内部方法】把当前内容作为撤销起点：清空历史，之后 Ctrl+Z 不会越过它。

        给 set_text / clear 这种"整体替换"用。Tk 内部把整块清空记成一步撤销，
        撤销它只会得到空内容（不是上一版内容），留着反而会造成困惑，
        所以整体写入后直接把历史重置掉。
        """
        try:
            self.text.edit_reset()
        except tk.TclError:
            pass

    def undo(self):
        """
        撤销上一步编辑（等价于按 Ctrl+Z）。

        说明：撤销的是"用户自己做的编辑"。程序写入的日志/文本（info、set_text 等）
        也会进入撤销栈，所以日志面板里 Ctrl+Z 也会逐步撤掉这些行；
        撤销到底后再按不会报错，只是内容不再变化。
        想清空撤销历史用 clear_undo_history()。
        """
        self._hotkey_undo(None)

    def redo(self):
        """重做被撤销的编辑（等价于按 Ctrl+Y）"""
        self._hotkey_redo(None)

    def clear_undo_history(self):
        """
        清空撤销历史：之后按 Ctrl+Z 不会再把内容改回去。

        适用场景：程序载入了新内容、重新渲染了整屏之后，
        不希望用户还能撤销到更早的状态时调用。
        说明：set_text / clear 内部已经会自动重置历史，
        这个方法用于"用 append/info 一行行写完之后"手动设一个新的撤销起点。
        """
        self._reset_undo_baseline()

    # ---------------- 字号缩放与布局保护 ----------------
    def _font_metrics(self):
        """返回当前字体的(单个字符宽度, 行高)，单位像素（内部方法）"""
        try:
            font = tkFont.Font(font=self.text.cget("font"))
            return max(1, font.measure("0")), max(1, font.metrics("linespace"))
        except tk.TclError:
            return max(1, self.font.measure("0")), max(1, self.font.metrics("linespace"))

    def _pin_requested_size(self):
        """
        【内部方法】把文本框向上汇报的"请求尺寸"钉死成当前实际像素尺寸。

        为什么需要它：
            Text 控件的请求尺寸是按"字符数 × 当前字体"换算的（默认 80 字符 × 24 行）。
            字号放大后，它换算出的像素请求会成倍膨胀，并沿 pack / grid 向上传播，
            抢走兄弟控件的空间 —— 表现就是分栏比例被破坏、左侧文件栏被挤没、
            滚动条错位。这里把请求尺寸换算成"当前分配到的像素对应的字符数"，
            于是不管字号怎么变，请求出去的像素尺寸都保持不变，布局完全不受影响。
        """
        try:
            px_w = self.text.winfo_width()
            px_h = self.text.winfo_height()
        except tk.TclError:
            return
        if px_w <= 1 or px_h <= 1:
            return  # 尚未完成布局，等下一次 Configure 再钉
        char_w, line_h = self._font_metrics()
        if px_w < 2 * char_w or px_h < 2 * line_h:
            # 尺寸小到连两个字都放不下，说明拿到的是"布局还没走完"的中间值，
            # 不是真实分配尺寸。此时如果照样钉住，面板之后的请求尺寸就永远是
            # 这个 2 像素，pack 也只给它 2 像素，面板会一直缩着长不回来。
            return
        want_w = max(1, px_w // char_w)
        want_h = max(1, px_h // line_h)

        try:
            cur_w = int(self.text.cget("width"))
            cur_h = int(self.text.cget("height"))
        except (tk.TclError, ValueError):
            cur_w = cur_h = -1
        if (want_w, want_h) == (cur_w, cur_h):
            return  # 已经是钉住的状态，避免反复设置引起布局抖动
        self.text.config(width=want_w, height=want_h)

    def _on_text_configure(self, event=None):
        """文本框尺寸变化回调：重钉请求尺寸，并让行号跟着重排（内部方法）"""
        self._pin_requested_size()
        self._schedule_gutter_redraw()

    def _on_panel_configure(self, event=None):
        """
        【内部方法】面板尺寸变化回调：把面板对外上报的尺寸钉成当前像素尺寸。

        为什么还需要这一层：
            文本框只能按"字符 × 字体"上报尺寸，换算时不足一行的零头会被丢掉
            （字号 40 时一行就是 60 多像素）。分栏容器拿到各分栏上报的尺寸后，
            会把"容器总高 - 各分栏上报之和"这个零头按权重重新分配，
            于是缩放字号时分栏比例会被轻微改动（实测约 30 像素的重排）。
            而 Frame 的 width/height 单位就是像素，可以做到精确相等：
            各分栏上报之和 == 容器尺寸 时零头为 0，分栏比例就一动不动了。
        """
        px_w = self.winfo_width()
        px_h = self.winfo_height()
        if px_w <= 1 or px_h <= 1:
            return  # 尚未完成布局，等下一次 Configure 再钉
        char_w, line_h = self._font_metrics()
        if px_w < 2 * char_w or px_h < 2 * line_h:
            # 同上：太小的尺寸是布局中间态，钉下去会让面板再也长不回来
            return
        if (px_w, px_h) == (self._pin_w, self._pin_h):
            return  # 已经钉好，避免反复设置引起布局抖动
        self._pin_w, self._pin_h = px_w, px_h
        self.config(width=px_w, height=px_h)
        # 关掉尺寸传递：本面板的大小由父容器决定，不再由内部文本框反推
        self.pack_propagate(False)

    def set_zoom(self, step: int):
        """
        按步长缩放字号（等价于 Ctrl+滚轮滚 step 格）。
        参数：
            step: 正数放大，负数缩小；字号自动限制在 MIN_FONT_SIZE ~ MAX_FONT_SIZE
        说明：
            只改字号和视口位置，不改变面板占用空间，父容器比例不会被打乱。
        """
        self._zoom_font(self.font_size + int(step))

    def _zoom_font(self, font_size: int):
        """【内部方法】应用新字号：只改字号与视口，不改控件占用空间"""
        font_size = max(self.MIN_FONT_SIZE, min(self.MAX_FONT_SIZE, int(font_size)))
        if font_size == self.font_size:
            return
        # 先记住当前视口相对位置，缩放后恢复，保证看到的内容不变
        y_top, _ = self.text.yview()

        self.font_size = font_size
        self.font.config(size=font_size)

        # 行号字体跟着字号变，缓存作废后重新生成
        self._gutter_font_cache = None
        self._gutter_digit_width = None
        self._gutter_width = 0

        # 关键：字号变了，请求尺寸必须按新字体重新换算并钉住，
        # 否则 Text 会按新字号膨胀出巨大的像素请求，把父容器布局撑坏
        self._pin_requested_size()
        self.text.yview_moveto(y_top)
        self._sync_modified_tracking()   # 行高变了，行号重新对齐

    def _mousewheel_zoom(self, event):
        """Ctrl+滚轮缩放字号：仅改字号，保留视口，布局不抖动"""
        step = 1 if event.delta > 0 else -1
        self._zoom_font(self.font_size + step)
        return "break"

    # ---------------- 日志文本API ----------------
    def pstr(self, msg: str, cl=True):
        """主线程打印普通字符串，自动换行（使用面板的正文颜色）"""
        self._writeln(f"{msg}\n" if cl else msg, "plain")

    def info(self, msg: str):
        """主线程打印INFO级别日志，自动滚动到底部（使用 info 类别颜色）"""
        self._writeln(f"[INFO] {msg}\n", "info")

    def warn(self, msg: str):
        """主线程打印WARN警告日志，自动滚动到底部（使用 warn 类别颜色，默认醒目黄）"""
        self._writeln(f"[WARN] {msg}\n", "warn")

    def error(self, msg: str):
        """主线程打印ERROR错误日志，自动滚动到底部（使用 error 类别颜色，默认醒目红）"""
        self._writeln(f"[ERROR] {msg}\n", "error")

    def log(self, msg: str, color: Optional[str] = None, prefix: str = ""):
        """
        打印一行文本，并**只给这一行**指定颜色（不动其它日志、也不改面板默认色）。

        这是"临时改一次颜色"的正确做法：不用 set_fg 改整个面板（那样之后写的
        所有内容都会跟着变），而是这一行单独上色。
        参数：
            msg: 文本内容
            color: 颜色名或 #RRGGBB；None 表示用正文色
            prefix: 行首前缀，例如 "[提示] "，默认为空
        示例：
            log.log("文件类型不是 .txt", color="#EE0000", prefix="[错误] ")
            log.log("已加载 120 行", color="#66CCFF", prefix="[提示] ")
        """
        self._writeln(f"{prefix}{msg}\n", "plain", color=color)

    def _writeln(self, text: str, level: str, color: Optional[str] = None):
        """
        【内部方法】写入一行日志：按类别上色，并滚动到底部。
        参数：
            text: 含结尾换行的文本
            level: 类别（info / warn / error / plain）
            color: 直接指定颜色（优先于类别配色）
        说明：
            这里不再调用 update_idletasks()：每写一行都强制刷新一遍界面，
            连续写日志时会从线性退化成平方级（实测 2000 行要 40 多秒）。
            see() 已经保证了滚动位置，重绘交给 Tk 的空闲周期即可。
        """
        self.insert_line(text, level=level, color=color)

    def safe_info(self, msg: str):
        """子线程安全版本info，子线程调用无需担心tk报错"""
        safe_call(self.root, self.info, msg)

    def safe_warn(self, msg: str):
        """子线程安全版本warn"""
        safe_call(self.root, self.warn, msg)

    def safe_error(self, msg: str):
        """子线程安全版本error"""
        safe_call(self.root, self.error, msg)

    def safe_log(self, msg: str, color: Optional[str] = None, prefix: str = ""):
        """子线程安全版本log（带颜色的单行日志）"""
        safe_call(self.root, self.log, msg, color, prefix)

    def insert_text(self, content: str):
        """追加文本，不会自动换行，在现有内容末尾添加（跟随正文色）"""
        self.append(content)

    def _hotkey_cut(self, event):
        """Ctrl+X 剪切（仅日志面板可编辑时需要）"""
        self.text.event_generate("<<Cut>>")
        return "break"

    def _hotkey_paste(self, event):
        """Ctrl+V 粘贴（仅日志面板可编辑时需要）"""
        self.text.event_generate("<<Paste>>")
        return "break"

    def _hotkey_save(self, event):
        """Ctrl+S 触发 on_save 回调"""
        if self.on_save is not None:
            self.on_save()
        return "break"

    # ---------------- 只读相关 ----------------
    def set_read_only(self, read_only: bool = True):
        """
        设置面板是否只读，并立即生效。

        只读时（True）：
            用户无法输入、退格删除、粘贴、剪切；
            但依然可以查看、鼠标选中、Ctrl+A 全选、Ctrl+C 复制、滚动浏览。
        只读不影响程序自身：
            set_text / clear / append / info / error 等仍然可以更新内容
            （内部会自动临时解锁、写完再锁上）。
        参数：
            read_only: True=只读；False=恢复可编辑
        示例：
            log = LogPanel(vsplit.bottom, read_only=True)   # 构造时直接只读
            log.set_read_only(False)                        # 临时允许编辑
        """
        self.read_only = bool(read_only)
        if self.read_only:
            # disabled 状态会挡掉用户的一切编辑操作，同时保留选中与复制
            self.text.config(state="disabled")
            self.text.update_idletasks()
        else:
            self.text.config(state="normal")

    def _writable_state(self) -> str:
        """
        【内部方法】准备写入内容：只读面板临时解锁，并返回需要还原的状态。

        同时会在撤销栈里插一个分隔符，把"这次写入"单独划成一步撤销 ——
        分隔符必须在写入**之前**插入：Tk 的 edit_undo 是回退到上一个分隔符处，
        写在后面会把这次写入和下一次写入算成同一步。
        返回 "normal" 表示本来就可写、无需还原；返回 "disabled" 表示
        这次是临时解锁的，写完必须调用 _restore_state 锁回去。
        """
        try:
            self.text.edit_separator()
        except tk.TclError:
            pass  # 控件已销毁或老版本 Tk，忽略
        if not self.read_only:
            return "normal"
        self.text.config(state="normal")
        return "disabled"

    def _restore_state(self, state: str):
        """【内部方法】写入完成后还原控件状态（只读面板重新锁上）"""
        if state == "disabled":
            self.text.config(state="disabled")
            self.text.update_idletasks()  # 立即重绘，避免锁上瞬间出现空白

    def append_line(self, text: str, color: Optional[str] = None):
        """
        在末尾追加一行内容（自动补换行），可指定这一行的颜色。
        参数：
            text: 文本内容，不需要自己带换行
            color: 颜色名或 #RRGGBB；None 表示跟随正文色
        """
        self.append(f"{text}\n", color=color)

    @property
    def native_widget(self):
        """底层原生ScrolledText控件，用来修改字体、颜色等原生属性"""
        return self.text
class ActionBar(tk.Frame):
    """
    横向操作条（工具栏 / 按钮行 / 表单行）

    【用途】一行里摆若干个按钮或"标签+输入框"的组合，随窗口变宽自动等宽排开。
    【布局规则】整条按"列"切：每个子元素占一列，列宽随窗口等分拉伸；
        子元素的高度保持自身需要的高度，不会被拉成一整条。
    【和分栏容器的区别】分栏容器是"按权重切两块"，操作条是"一格一个控件排一行"。
    参数：
        master: 父容器
        padx / pady: 内容四周留白（像素）
        spacing: 相邻元素之间的间距（像素）
    方法：
        add_label(text, ...)：加一个文字标签
        add_button(text, on_click, ...)：加一个按钮
        add_entry(textvariable=None, width=12, ...)：加一个单行输入框
        add_space(...)：加一段弹性空白（把后面的元素挤到右边）
        add_separator(...)：加一条竖分隔线
        clear()：清掉条上的全部元素
        widgets：当前条上所有元素的列表
    属性：
        .to_end：右侧追加标记，赋值 True 后新增的元素都排到右边（见 add 的 to_end）
    示例：
        bar = ActionBar(main.top)
        main.top.add(bar)
        bar.add_button('打开 / 克隆', on_open, expand=True)
        bar.add_button('刷新', on_refresh, expand=True)
        bar.add_label('仓库地址：')
        bar.add_entry(addr_var, expand=True, width=40)
        bar.to_end = True          # 之后的元素都靠右
        bar.add_button('设置', on_settings)
    """
    # 复合控件标记：被 add() 添加时自动铺满所在格子（见 _is_filling）
    _mytkui_composite = True

    def __init__(self, master, padx: int = 6, pady: int = 5, spacing: int = 4, **kwargs):
        super().__init__(master, **kwargs)
        self._padx = max(0, int(padx))
        self._pady = max(0, int(pady))
        self._spacing = max(0, int(spacing))
        self._widgets = []            # [(控件, 是否靠右)]
        self.to_end = False
        # 内容四周留白用内嵌容器实现，避免逐个元素算 padx/pady
        self._inner = tk.Frame(self)
        self._inner.pack(fill=tk.BOTH, expand=True,
                         padx=self._padx, pady=self._pady)
        # 靠右的那一组单独放在一个容器里：容器贴最右，组内元素自然从左到右排，
        # 既保持添加顺序，也不会因为重新 pack 而抖动
        self._end_group = tk.Frame(self._inner)
        self._gap = None              # 左右两组之间的弹性空白

    # ---------------- 添加元素 ----------------
    def add(self, widget: tk.Widget, expand: bool = True,
            to_end: Optional[bool] = None, side: str = "left"):
        """
        往条上添加一个元素，横向排在当前这一行里。

        参数：
            widget: 子控件（按钮、标签、输入框，或任何控件）
            expand: True（默认）=占满分到的空间（多个元素等分多余宽度）；
                    False=只占自身宽度
            to_end: True=放进右侧那一组（贴到最右边）；False/None=接着往右排
                    （None 时看 self.to_end 的当前值）
            side: "left" / "right" 的简写，"right" 等价于 to_end=True
        返回：
            传入的 widget，便于链式写法
        """
        if to_end is None:
            to_end = self.to_end or (str(side).lower() == "right")
        if to_end and self._gap is None:
            # 第一次出现靠右元素：在左右两组之间插一段弹性空白，
            # 把左组挤到左边、右组推到最右
            self._gap = tk.Frame(self._inner)
            self._gap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self._end_group.pack(side=tk.RIGHT, fill=tk.Y)
        parent = self._end_group if to_end else self._inner
        parent.pack_propagate(True)
        widget.pack(side=tk.LEFT, fill=(tk.BOTH if expand else tk.Y),
                    expand=expand, padx=(self._spacing, 0))
        self._widgets.append((widget, to_end))
        self._notify_owner()
        return widget

    def _notify_owner(self):
        """
        【内部方法】内容变了，通知所在的应用骨架重新测量这一条需要多高。

        为什么要通知：工具条是放在 AppShell 顶部那种"按内容定高"的区域里的，
        父区域早就按旧高度把自己钉住了；新加进来的元素如果不触发一次重算，
        就会一直被压在旧高度里（表现为按钮只剩 1 像素高）。
        实现上往上找 _mytkui_shell 标记的父容器，找到就让它重算一次；
        不在 AppShell 里（单独使用工具条）就什么都不做。
        """
        widget = self
        while widget is not None:
            owner = getattr(widget, "_mytkui_shell", None)
            if owner is not None:
                try:
                    owner._schedule_sync_heights()
                except (AttributeError, tk.TclError):
                    pass
                return
            widget = getattr(widget, "master", None)


    def add_label(self, text: str, expand: bool = False, width: Optional[int] = None,
                  fg: Optional[str] = None, **kwargs):
        """
        添加一个文字标签。
        参数：
            text: 标签文字
            expand: 是否占满自己那一列
            width: 固定宽度（字符数）；None=按文字自动
            fg: 文字颜色
            **kwargs: 其余参数直接透传给 tk.Label（font、bg、anchor……）
        """
        label = tk.Label(self._inner, text=text, fg=fg, **kwargs)
        if width is not None:
            label.config(width=width)
        return self.add(label, expand=expand)

    def add_button(self, text: str, on_click=None, expand: bool = True,
                   width: Optional[int] = None, **kwargs):
        """
        添加一个按钮。
        参数：
            text: 按钮文字
            on_click: 点击回调（无参数）
            expand: 是否占满自己那一列（默认 True，多个按钮会等宽排开）
            width: 固定宽度（字符数）
            **kwargs: 其余参数直接透传给 tk.Button
        返回：
            底层 tk.Button（要改文字/状态用它）
        """
        def handle():
            if on_click is not None:
                on_click()

        button = tk.Button(self._inner, text=text, command=handle, **kwargs)
        if width is not None:
            button.config(width=width)
        self.add(button, expand=expand)
        return button

    def add_entry(self, textvariable=None, expand: bool = True, width: int = 12, **kwargs):
        """
        添加一个单行输入框。
        参数：
            textvariable: 绑定用的 StringVar（推荐传，方便取值）
            expand: 是否占满自己那一列（默认 True，输入框适合拉长）
            width: 宽度（字符数），仅在 expand=False 时有意义
            **kwargs: 其余参数直接透传给 tk.Entry（show、state……）
        返回：
            底层 tk.Entry
        """
        entry = tk.Entry(self._inner, textvariable=textvariable, width=width, **kwargs)
        if textvariable is None:
            entry.config(width=width)
        self.add(entry, expand=expand)
        return entry

    def add_space(self, weight: int = 1, **kwargs):
        """
        添加一段弹性空白，用来把后面的元素挤到右边。

        参数：
            weight: 空白所占的拉伸权重：想留两段空白时，
                    传 (1, 2) 就是"前一段占 1 份、后一段占 2 份"的宽度比例。
                    只加一段时随便传 1 就行。
        返回：
            第一段空白用的 Frame（后面几段可通过 .extra_spacers 取到）
        说明：
            实际做法是并排放 weight 个同样可伸缩的小空白 —— pack 本身
            不支持给单个控件设权重，用数量近似即可，视觉效果一致。
        """
        count = max(1, int(weight))
        spacers = []
        for _ in range(count):
            spacer = tk.Frame(self._inner, **kwargs)
            spacer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            spacers.append(spacer)
            self._widgets.append((spacer, False))
        return spacers[0]

    def add_separator(self, **kwargs):
        """添加一条竖向分隔线（视觉分组用）"""
        line = tk.Frame(self._inner, width=2, bd=0, highlightthickness=0,
                        bg=kwargs.pop("bg", "#c9c9c9"), **kwargs)
        line.pack(side=tk.LEFT, fill=tk.Y, padx=(self._spacing, 0))
        self._widgets.append((line, False))
        return line

    def clear(self):
        """清掉条上的全部元素（左右分组一并重置）"""
        for widget, _ in self._widgets:
            widget.destroy()
        self._end_group.destroy()
        if self._gap is not None:
            self._gap.destroy()
            self._gap = None
        # 重建右组容器，供后续继续使用
        self._end_group = tk.Frame(self._inner)
        self._widgets = []
        self.to_end = False

    @property
    def widgets(self) -> list:
        """条上当前的元素列表（按添加顺序）"""
        return [w for w, _ in self._widgets]


class StatusBar(tk.Frame):
    """
    底部状态栏：左边显示状态文字，右边可选显示补充信息（分支名、文件数……）

    【用途】给窗口底部放一条"当前在干什么"的提示，配合 TASK 使用可显示进度。
    【布局规则】左中右三栏：左栏靠左、中栏铺满中间、右栏靠右。
    参数：
        master: 父容器
        text: 初始状态文字
        bg / fg: 背景色 / 文字色（默认浅灰底深灰字，若父容器是深色主题可自行指定）
        padx / pady: 内容留白
    方法：
        set(text)：改状态文字
        get()：读当前状态文字
        set_right(text)：改右侧补充信息
        flash(text, ms=2000)：临时显示一条信息，到点后自动恢复原状态
        clear()：清空状态文字
    属性：
        .label：左侧状态文字标签
        .right_label：右侧补充信息标签
    """
    # 复合控件标记：被 add() 添加时自动铺满所在格子（见 _is_filling）
    _mytkui_composite = True

    def __init__(self, master, text: str = "就绪", bg: str = "#f0f0f0",
                 fg: str = "#333333", padx: int = 8, pady: int = 3, **kwargs):
        super().__init__(master, bg=bg, highlightthickness=0, bd=0, **kwargs)
        self._default_text = text
        self._flash_job = None
        self.grid_columnconfigure(1, weight=1)   # 中间那一列吃掉多余宽度
        self.label = tk.Label(self, text=text, bg=bg, fg=fg, anchor="w")
        self.label.grid(row=0, column=0, sticky="w", padx=(padx, 4), pady=pady)
        self.right_label = tk.Label(self, text="", bg=bg, fg=fg, anchor="e")
        self.right_label.grid(row=0, column=2, sticky="e", padx=(4, padx), pady=pady)

    def set(self, text: str):
        """设置状态文字（同时会取消未到点的 flash 恢复）"""
        self._cancel_flash()
        self._default_text = text
        self.label.config(text=text)

    def get(self) -> str:
        """读取当前状态文字"""
        return self.label.cget("text")

    def set_right(self, text: str):
        """设置右侧补充信息（分支名、文件数、耗时等）"""
        self.right_label.config(text=text)

    def flash(self, text: str, ms: int = 2000):
        """
        临时显示一条信息，到点后自动恢复成之前的状态文字。
        参数：
            text: 要临时显示的内容
            ms: 显示多少毫秒（默认 2000）
        """
        self._cancel_flash()
        self.label.config(text=text)

        def restore():
            self._flash_job = None
            try:
                self.label.config(text=self._default_text)
            except tk.TclError:
                pass

        try:
            self._flash_job = self.after(max(1, int(ms)), restore)
        except tk.TclError:
            self._flash_job = None

    def clear(self):
        """清空状态文字"""
        self.set("")

    def _cancel_flash(self):
        """【内部方法】取消还没到点的 flash 恢复任务"""
        if self._flash_job is not None:
            try:
                self.after_cancel(self._flash_job)
            except tk.TclError:
                pass
            self._flash_job = None


class PageBook(tk.Frame):
    """
    多页签容器（Notebook）

    【用途】把多块内容叠在同一区域，用户点页签切换，省空间。
    【和分栏容器的区别】分栏是"同时看见几块"，页签是"一次只看见一块"。
    参数：
        master: 父容器
        tab_side: 页签位置，"top"（默认）/ "bottom" / "left" / "right"
        padx / pady: 每页内容四周的留白（像素）
    方法：
        add_page(title) -> _BoxFrame       添加一页，返回该页的容器（支持 .add()）
        remove_page(title)                 删除一页
        show(title)                        切换到某一页
        current_title()                    当前页的标题
        titles()                           所有页标题（按添加顺序）
        page(title)                        取某一页的容器
    属性：
        .notebook：底层 ttk.Notebook（要更细的控制时用）
    示例：
        book = PageBook(main.right)
        main.right.add(book)
        page1 = book.add_page('变更')
        page1.add(LogPanel(page1), expand=True)
        page2 = book.add_page('历史')
        page2.add(LogPanel(page2), expand=True)
        book.show('历史')
    """
    # 复合控件标记：被 add() 添加时自动铺满所在格子（见 _is_filling）
    _mytkui_composite = True

    def __init__(self, master, tab_side: str = "top", padx: int = 2, pady: int = 2, **kwargs):
        super().__init__(master, **kwargs)
        from tkinter import ttk as _ttk
        self._padx = max(0, int(padx))
        self._pady = max(0, int(pady))
        self._pages = {}          # 标题 -> 页面容器
        self.notebook = _ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

    def add_page(self, title: str) -> "_BoxFrame":
        """
        添加一页并返回它的容器（_BoxFrame，支持 .add()）。
        参数：
            title: 页签上显示的文字（重复会覆盖同一页的容器）
        """
        if title in self._pages:
            raise ValueError(f"页签 {title!r} 已经存在了")
        holder = tk.Frame(self.notebook)
        self.notebook.add(holder, text=title)
        # 页面内容用 _BoxFrame 承载，这样它和分栏格子的 .add() 行为完全一致
        page = _BoxFrame(holder)
        page.pack(fill=tk.BOTH, expand=True, padx=self._padx, pady=self._pady)
        self._pages[title] = page
        return page

    def remove_page(self, title: str):
        """删除一页（标题不存在也不会报错）"""
        page = self._pages.pop(title, None)
        if page is None:
            return
        holder = page.master
        try:
            self.notebook.forget(holder)
        except tk.TclError:
            pass
        holder.destroy()

    def show(self, title: str):
        """切换到某一页（标题不存在时忽略，不抛异常）"""
        page = self._pages.get(title)
        if page is None:
            return
        try:
            self.notebook.select(page.master)
        except tk.TclError:
            pass

    def current_title(self) -> str:
        """返回当前显示页的标题；没有页时返回空字符串"""
        try:
            selected = self.notebook.select()
        except tk.TclError:
            return ""
        for title, page in self._pages.items():
            if str(page.master) == str(selected):
                return title
        return ""

    def titles(self) -> list:
        """所有页标题（按添加顺序）"""
        return list(self._pages.keys())

    def page(self, title: str):
        """取某一页的容器；不存在返回 None"""
        return self._pages.get(title)


class CommitDialog(tk.Toplevel):
    """
    通用表单对话框：填若干项，点确定后返回结果字典

    【用途】"提交信息 + 作者 + 两个勾选项"这类对话框，不必每次手写一个 Toplevel。
    【特点】
        模态（弹窗期间主窗口不可点）、自动相对父窗口居中、按 Esc 取消、
        回车提交（多行文本框内回车换行、不提交）、关闭按钮等同取消。
    参数：
        master: 父窗口（一般为 AppWindow.root，或某个控件）
        title: 窗口标题
        fields: 表项列表，每项是一个字典：
            类型   "label"   → text
                    "input"   → text（标签）、value（默认值）、width
                    "text"    → text（标签）、value（默认值）、height（行数，默认 5）
                    "check"   → text（勾选项文字）、value（默认是否勾选）
                    其它值（"buttons"）→ 自定义按钮行，buttons 是 [(文字, 回调)]
        buttons: 底部按钮，默认 [("确定", None), ("取消", None)]
                    （名字为"取消"的按钮自动绑定为关闭对话框）
        ok_text / cancel_text: 想用别的名字时的简写
    方法：
        show() -> Optional[dict]    显示对话框并阻塞，点确定返回 {键: 值}，取消返回 None
        close(result=None)          程序里主动关闭对话框
    结果字典的键：
        "input"/"text" 类的项用它的 text 作键，值为字符串；"check" 类为 True/False
    用法：
        dlg = CommitDialog(window.root, "提交更改", [
            {"type": "text",  "text": "提交信息：", "value": "本次提交的说明…", "height": 6},
            {"type": "input", "text": "作者（可选）："},
            {"type": "check", "text": "提交并推送到远程", "value": False},
        ])
        result = dlg.show()
        if result is not None:
            message = result["提交信息："]
            push = result["提交并推送到远程"]
        若还需要自定义底部按钮：
            dlg.add_button("仅暂存", on_stash)      # 在 show() 之前调用
    """
    def __init__(self, master, title: str = "请输入", fields=None, buttons=None,
                 ok_text: str = "确定", cancel_text: str = "取消",
                 width: int = 480, **kwargs):
        super().__init__(master, **kwargs)
        self.title(title)
        self._result: Optional[dict] = None
        self._rows = []            # [(键, 取值函数)]
        self._extra_buttons = []   # [(文字, 回调)]

        # 相对于父窗口居中，避免对话框跑到屏幕外或主窗口后面"看不见"
        try:
            self.transient(master.winfo_toplevel())
        except (AttributeError, tk.TclError):
            pass
        try:
            self.grab_set()        # 模态
        except tk.TclError:
            pass

        body = tk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=(14, 6))
        for field in (fields or []):
            self._build_field(body, field)

        self._button_row = tk.Frame(self)
        self._button_row.pack(fill=tk.X, padx=14, pady=(0, 12))
        names = buttons or [(ok_text, None), (cancel_text, None)]
        for text, callback in names:
            is_cancel = (text == cancel_text)
            self._button_row_add(text, (lambda: self.close(None)) if is_cancel else callback,
                                 primary=not is_cancel)

        self.protocol("WM_DELETE_WINDOW", lambda: self.close(None))
        self.bind("<Escape>", lambda _e: self.close(None))
        self.bind("<Return>", self._on_return)
        self._place_window(master, width)

    # ---------------- 内部：构建表项 ----------------
    def _build_field(self, body: tk.Frame, field: dict):
        """【内部方法】按描述构建一个表项"""
        kind = str(field.get("type", "input")).lower()
        if kind == "label":
            tk.Label(body, text=field.get("text", ""), anchor="w").pack(fill=tk.X, pady=(6, 2))
        elif kind == "input":
            tk.Label(body, text=field.get("text", ""), anchor="w").pack(fill=tk.X, pady=(6, 2))
            var = tk.StringVar(value=str(field.get("value", "")))
            entry = tk.Entry(body, textvariable=var, width=int(field.get("width", 40)))
            entry.pack(fill=tk.X)
            self._rows.append((field.get("text", ""), var.get))
        elif kind == "text":
            tk.Label(body, text=field.get("text", ""), anchor="w").pack(fill=tk.X, pady=(6, 2))
            box = tk.Text(body, height=int(field.get("height", 5)), wrap=tk.WORD)
            box.pack(fill=tk.BOTH, expand=True)
            box.insert("1.0", str(field.get("value", "")))
            key = field.get("text", "")

            def read_text(box=box):
                return box.get("1.0", "end-1c")

            self._rows.append((key, read_text))
        elif kind == "check":
            var = tk.BooleanVar(value=bool(field.get("value", False)))
            tk.Checkbutton(body, text=field.get("text", ""), variable=var,
                           anchor="w").pack(fill=tk.X, pady=(6, 0))
            self._rows.append((field.get("text", ""), var.get))
        elif kind == "buttons":
            row = tk.Frame(body)
            row.pack(fill=tk.X, pady=(8, 0))
            for text, callback in field.get("buttons", []):
                tk.Button(row, text=text, command=callback).pack(side=tk.LEFT, padx=(0, 6))
        # 其它类型忽略，不抛异常：写错一个键不至于让整个对话框起不来

    def add_button(self, text: str, on_click=None):
        """
        在底部按钮行追加一个自定义按钮（需在 show() 之前调用）。
        参数：
            text: 按钮文字
            on_click: 点击回调；对话框不会因为点它而关闭（要关闭自己调 close()）
        返回：
            底层 tk.Button
        """
        return self._button_row_add(text, on_click, primary=False)

    def _button_row_add(self, text: str, callback, primary: bool):
        """【内部方法】往按钮行加一个按钮"""
        def handle():
            if callback is not None:
                callback()
        button = tk.Button(self._button_row, text=text, command=handle)
        button.pack(side=tk.LEFT, padx=(0, 6))
        if primary:
            button.config(default=tk.ACTIVE)   # 回车键触发
        return button

    def _on_return(self, event=None):
        """【内部方法】回车提交；在多行文本框里回车应该是换行，不提交"""
        if isinstance(event.widget, tk.Text):
            return None
        self._ok()
        return "break"

    def _place_window(self, master, width: int):
        """【内部方法】设置尺寸并相对父窗口居中"""
        self.update_idletasks()
        height = max(140, self.winfo_reqheight())
        self.geometry(f"{int(width)}x{int(height)}")
        try:
            parent = master.winfo_toplevel()
            px, py = parent.winfo_rootx(), parent.winfo_rooty()
            pw, ph = parent.winfo_width(), parent.winfo_height()
            x = max(0, px + (pw - int(width)) // 2)
            y = max(0, py + (ph - int(height)) // 3)
            self.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass

    # ---------------- 对外接口 ----------------
    def _ok(self):
        """【内部方法】收集结果并关闭"""
        data = {}
        for key, getter in self._rows:
            try:
                data[key] = getter()
            except tk.TclError:
                data[key] = None
        self.close(data)

    def close(self, result=None):
        """关闭对话框；result 会作为 show() 的返回值"""
        self._result = result
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

    def show(self):
        """
        显示对话框并阻塞，直到用户点确定/取消或关闭窗口。
        返回：
            点确定 → {键: 值} 字典；取消/关闭 → None（空输入不会自动判空，
            需要校验请在自己的逻辑里判断）
        """
        try:
            self.wait_window(self)
        except tk.TclError:
            return None
        return self._result


# DialogBox：CommitDialog 的别名，写起来短一点，语义也更通用
DialogBox = CommitDialog


class _ShellRegion(_BoxFrame):
    """
    【内部类】AppShell 的上/下区域容器。

    比普通的 _BoxFrame 多做一件事：被添加控件时通知所属的 AppShell
    重新测量这一条需要多高 —— 否则后加进去的工具条会因为父容器还按
    旧高度摆放而被压成一条线。
    """
    def __init__(self, master, owner):
        super().__init__(master)
        self._owner = owner

    def add(self, widget: tk.Widget, expand: bool = False):
        """加控件后顺手让 AppShell 重算一次高度"""
        result = super().add(widget, expand=expand)
        owner = self._owner
        if owner is not None:
            owner._schedule_sync_heights()
        return result


class AppShell(tk.Frame):
    """
    标准应用骨架：顶部操作区 + 中间内容区 + 底部状态栏

    【用途】三分钟搭出一个像样的应用框架，不用每次手工堆工具栏和状态栏。
    【布局规则】
        顶部：以自然高度固定在窗口上方，随窗口变宽而变宽（工具条类控件）。
        中间：吃掉全部剩余空间（放分栏容器、页签、面板都行）。
        底部：以自然高度固定在窗口下方。
    参数：
        master: 父容器（一般传 window.root）
        status: 初始状态栏文字
        padx / pady: 三块各自的留白
        status_bar: 传 False 表示不要底部状态栏
    属性：
        .top：顶部区域（_BoxFrame，支持 .add()）
        .content：中间内容区（_BoxFrame，支持 .add()）
        .bottom：底部区域（_BoxFrame，支持 .add()）
        .status_bar：底部状态栏（StatusBar；不要状态栏时为 None）
    方法：
        set_status(text) / get_status()：读写状态栏文字
        flash_status(text, ms=2000)：状态栏临时提示
        use_content(widget)：往内容区添加控件（等价 content.add(widget, expand=True)）
    示例：
        window = AppWindow('Git 管理器', 1000, 700)
        shell = AppShell(window.root, status='就绪')
        window.add(shell, expand=True)

        bar = ActionBar(shell.top)
        shell.top.add(bar, expand=False)
        bar.add_button('刷新', on_refresh, expand=True)

        main = HSplitFrame(shell.content)
        shell.content.add(main, expand=True)

        shell.set_status('已加载')
        shell.status_bar.set_right('master')
    """
    # 复合控件标记：被 add() 添加时自动铺满所在格子（见 _is_filling）
    _mytkui_composite = True

    def __init__(self, master, status: str = "就绪", padx: int = 0, pady: int = 0,
                 status_bar: bool = True, **kwargs):
        super().__init__(master, **kwargs)
        self.pack_propagate(False)
        self.grid_propagate(False)
        self._pad = (max(0, int(padx)), max(0, int(pady)))
        self._sync_job = None

        # 三块都用 pack 竖直叠放：top/bottom 只占内容需要的高度，
        # content 用 expand=True 吃掉全部剩余空间
        self.top = _ShellRegion(self, self)
        self.top.pack(side=tk.TOP, fill=tk.X, expand=False,
                      padx=self._pad[0], pady=(self._pad[1], 0))

        self.bottom = _ShellRegion(self, self)
        self.bottom.pack(side=tk.BOTTOM, fill=tk.X, expand=False,
                         padx=self._pad[0], pady=(0, self._pad[1]))

        self.content = _BoxFrame(self)
        self.content.pack(side=tk.TOP, fill=tk.BOTH, expand=True,
                          padx=self._pad[0], pady=(self._pad[1], self._pad[1]))
        self.content.pack_propagate(False)

        # 让三个区域都能往上找到本 shell：工具条等控件内容变化时靠它触发高度重算
        for region in (self.top, self.content, self.bottom):
            setattr(region, "_mytkui_shell", self)

        self.status_bar = StatusBar(self.bottom, text=status) if status_bar else None
        if self.status_bar is not None:
            self.bottom.add(self.status_bar, expand=False)

        # 有内容进来或尺寸变化时，重新算一次顶部/底部需要多高
        for frame in (self.top, self.bottom):
            frame.bind("<Configure>", self._on_region_configure, add="+")
        self.bind("<Configure>", self._on_self_configure, add="+")
        self.after_idle(self._sync_heights)

    # ---------------- 尺寸维护 ----------------
    def sync_layout(self):
        """
        立即重新测量顶部/底部区域的高度。

        什么时候需要手动调：往工具条里"又加了元素"之后（例如
        bar.add_button(...)），如果希望立刻看到正确高度就调一下；
        不调也行 —— 面板会在空闲时自动重算，只是可能晚一帧。
        """
        self._sync_heights()

    def _on_region_configure(self, event=None):
        """【内部方法】顶部/底部内容变化后，重新上报它们需要的高度"""
        self._schedule_sync_heights()

    def _on_self_configure(self, event=None):
        """【内部方法】自身体积变化后，也让顶部/底部重新上报一次"""
        self._schedule_sync_heights()

    def _schedule_sync_heights(self):
        """
        【内部方法】把"重新测量顶部/底部高度"推迟到空闲时做一次。

        为什么不能直接算：调用方往往紧接着还要往工具条里加按钮，
        每个按钮加完都重算一遍没有必要；合并到空闲时算，既跟手又省事。
        """
        if self._sync_job is not None:
            return
        try:
            self._sync_job = self.after_idle(self._run_sync_heights)
        except tk.TclError:
            self._sync_job = None

    def _run_sync_heights(self):
        """【内部方法】真正执行一次高度重算"""
        self._sync_job = None
        self._sync_heights()
        # 重算完再把自身请求尺寸同步一次：AppShell 关掉了尺寸传递，
        # 不主动上报的话，父容器（分栏格子/主窗口）不知道该给它多大
        self._report_natural_size()

    def _sync_heights(self):
        """
        【内部方法】把顶部/底部区域的高度钉成"内容需要的高度"。

        为什么要钉：AppShell 关掉了尺寸传递（pack_propagate(False)），
        Frame 不会自己把子控件高度反映上去；不显式上报的话，顶部区域
        会被算成 1 像素（工具条被压扁），或者反过来把内容区挤没。
        """
        for frame in (self.top, self.bottom):
            try:
                height = max(1, frame.measure_now("h"))
                if int(frame.cget("height")) != height:
                    frame.config(height=height)
            except tk.TclError:
                return

    def _report_natural_size(self):
        """【内部方法】对外上报"顶部 + 内容 + 底部"的自然尺寸（供父容器布局）"""
        try:
            height = (self.top._natural_size("h") + self.content._natural_size("h")
                      + self.bottom._natural_size("h"))
            width = max(self.top._natural_size("w"), self.content._natural_size("w"),
                        self.bottom._natural_size("w"))
            self.config(width=max(1, width), height=max(1, height))
        except tk.TclError:
            pass

    def add(self, widget: tk.Widget, expand: bool = False):
        """
        向内容区添加控件（等价于 self.content.add(...)），方便像普通容器一样使用。
        """
        return self.content.add(widget, expand=expand)

    def use_content(self, widget: tk.Widget, expand: bool = True):
        """往内容区添加控件（默认铺满），返回该控件"""
        self.content.add(widget, expand=expand)
        return widget

    # ---------------- 状态栏快捷方法 ----------------
    def set_status(self, text: str):
        """设置底部状态栏文字（没有状态栏时什么都不做）"""
        if self.status_bar is not None:
            self.status_bar.set(text)

    def get_status(self) -> str:
        """读取底部状态栏文字（没有状态栏时返回空串）"""
        return self.status_bar.get() if self.status_bar is not None else ""

    def flash_status(self, text: str, ms: int = 2000):
        """底部状态栏临时提示，到点自动恢复（没有状态栏时什么都不做）"""
        if self.status_bar is not None:
            self.status_bar.flash(text, ms)





class FileSelect(tk.Frame):
    """
    文件选择控件：标签 + 输入框 + "选择"按钮
    点击【选择】按钮，弹出系统文件选择对话框，选中文件后触发on_select回调
    参数：
        master: 父容器
        label: 左侧显示的文字标签
        auto_create: 选中的文件不存在时是否自动创建空文件，默认 False 不创建。
                     要创建的文件类型由"用户填入的路径后缀"决定：
                     路径写成 D:\\x\\demo.asm 就创建 demo.asm，写成 demo.txt 就创建 demo.txt。
                     父目录不存在、没有写权限等情况不会报错，路径照常返回，
                     具体原因可以通过 last_error 查看。
    成员：
        .on_select: 回调函数，选中文件后自动调用，传入文件路径字符串
        .last_error: 最近一次自动创建失败的原因（没有失败则为空字符串）
    方法：
        get_path()：获取当前选择的文件路径
        set_path(path)：手动设置文件路径
        ensure_exists(path=None)：按需创建文件（不存在才建），返回文件路径
        ask_file(...)：弹出对话框让用户选文件，并返回文件路径字符串
                       【可以在子线程里安全调用，见下面的说明和示例】
    属性：
        .native_entry：底层原生Entry单行输入框
    """
    def __init__(self, master, label: str, auto_create: bool = False, **kwargs):
        super().__init__(master, **kwargs)
        self.root = self.winfo_toplevel()
        self.on_select: Optional[Callable[[str], Any]] = None
        # 选中的文件不存在时是否自动创建（文件类型由路径后缀决定）
        self.auto_create = bool(auto_create)
        # 最近一次自动创建失败的原因，方便调用方提示用户
        self.last_error = ""

        self.var = tk.StringVar()
        tk.Label(self, text=label).pack(side=tk.LEFT, padx=3)
        self.entry = tk.Entry(self, textvariable=self.var)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)
        tk.Button(self, text="选择", command=self._on_btn).pack(side=tk.LEFT, padx=2)
        # 对话框用的是 tkinter 的 askopenfilename：它只能选"已存在的文件"。
        # 所以绑上"保存文件"对话框，用户可以直接输入新文件名（例如 demo.asm），
        # 这样"自动创建"才有实际用武之地；没开自动创建时保持原来的选择行为。
        self._dialog_func = (filedialog.asksaveasfilename if self.auto_create
                             else filedialog.askopenfilename)

    def _on_btn(self):
        """内部按钮点击事件，用户不要直接调用"""
        path = self._dialog_func(title="选择文件")
        if not path:
            return
        self._accept_path(path)

    def ensure_exists(self, path: Optional[str] = None) -> str:
        """
        确保文件存在：文件不存在时按需创建（默认用输入框里的路径）。

        参数：
            path: 文件路径；None 表示用输入框当前内容
        返回：
            处理后的文件路径字符串；路径为空、已存在、或创建失败时会原样返回路径，
            不抛异常。创建失败的原因记在 self.last_error 里。
        说明：
            创建的是**空文件**；文件类型完全由路径后缀决定（.asm / .txt / …），
            本方法不限制后缀。父目录不存在时不会去创建目录，只会记录错误。
        """
        self.last_error = ""
        target = self.var.get() if path is None else path
        target = (target or "").strip()
        if not target:
            return ""
        try:
            file_path = Path(target)
            if not file_path.exists():
                # 只建文件、不建目录：用户给的目录不对时要让他知道，而不是悄悄造目录
                file_path.touch(exist_ok=True)
        except OSError as exc:
            # 父目录不存在、无写权限、路径非法等：不抛给调用方，只记录原因
            self.last_error = str(exc)
        return target

    def _accept_path(self, path: str, auto_create: Optional[bool] = None) -> str:
        """
        【内部方法】接收一个选中的路径：回填输入框、按需创建文件、触发回调。
        参数：
            path: 对话框返回的文件路径
            auto_create: 是否自动创建文件；None=沿用构造时的设置
        返回：
            处理后的路径（创建失败也照常返回，原因见 self.last_error）
        """
        self.var.set(path)
        if self.auto_create if auto_create is None else auto_create:
            self.ensure_exists(path)
        if self.on_select is not None:
            self.on_select(path)
        return path

    def _default_extension(self, filetypes) -> str:
        """
        【内部方法】从 filetypes 里取出默认后缀（例如 [("汇编", "*.asm")] → ".asm"）。

        作用：用了"保存"对话框时，用户只输入 demo，系统会自动补成 demo.asm，
        这样"文件类型由路径后缀决定"这件事对用户更省事。
        取不到就返回空串（不强制补后缀，用户写什么就是什么）。
        """
        if not filetypes:
            return ""
        try:
            pattern = str(filetypes[0][1])
        except (IndexError, TypeError, KeyError):
            return ""
        for part in pattern.replace(";", " ").split():
            if part.startswith("*.") and len(part) > 2:
                return part[1:]  # "*.asm" -> ".asm"
        return ""

    def ask_file(self, title: str = "选择文件",
                 filetypes=None,
                 initialdir: Optional[str] = None,
                 timeout: Optional[float] = None,
                 auto_create: Optional[bool] = None) -> str:
        """
        【可在子线程安全调用】弹出系统文件选择对话框，返回选中的文件路径。

        参数：
            title: 对话框标题，默认"选择文件"
            filetypes: 文件类型过滤，例如 [("文本文件", "*.txt"), ("所有文件", "*.*")]
            initialdir: 打开时定位到的目录，默认用输入框里当前的目录
            timeout: 等待主线程弹出对话框的秒数；None=一直等（默认）
            auto_create: 选中的文件不存在时是否自动创建空文件。
                         None（默认）=沿用构造 FileSelect 时的设置；
                         True/False=只对本次调用生效。
                         创建的文件类型由"用户填入的路径后缀"决定。
        返回：
            选中的文件路径字符串；用户取消或超时返回 ""（空字符串）

        为什么需要它：
            tkinter 只能在主线程操作界面，子线程直接弹对话框会报错甚至崩溃。
            这个方法内部把对话框投递到主线程执行，子线程**阻塞等待**结果，
            再像普通函数一样把路径返回给你，所以子线程里可以这样写：
                path = self.fileselect.ask_file(title="选择要汇编的文件")
                if path: ...
        调用效果：
            与点击【选择】按钮一致 —— 会把路径填进输入框、按需创建文件、
            并触发 on_select 回调。
        注意：
            子线程调用时会一直等到用户选完（或超时）才返回；
            主线程自己调用时会直接弹出对话框（不会卡死）；
            如果窗口已经关闭、或主线程还没启动消息循环（mainloop 未运行），
            会立即返回 ""。
        """
        result = {"path": "", "done": threading.Event()}
        # 本次调用是否自动创建：没显式指定就用构造时的设置
        want_create = self.auto_create if auto_create is None else bool(auto_create)

        # 窗口已经销毁就直接返回：销毁后 after()/StringVar.set() 不报错但也不生效，
        # 不先拦一下的话，子线程会拿到一个"看起来成功、其实界面已经没了"的路径。
        #
        # winfo_exists() 在两种情况会抛异常，都按"窗口不可用"处理：
        #   TclError    —— 窗口已经销毁；
        #   RuntimeError—— 该查询要注册 Tcl 命令，而主线程还没进 mainloop
        #                  （此时子线程既查不了、也没人执行投递过去的对话框）。
        # 如果这里放着不管，子线程会被异常打挂，这比返回空串糟糕得多。
        try:
            if not self.winfo_exists():
                return ""
        except (tk.TclError, RuntimeError):
            return ""

        def show_dialog() -> str:
            """【在主线程执行】真正弹出对话框，并返回选中的路径（取消为空串）"""
            try:
                # 要自动创建文件时用"保存"对话框：原生"打开"对话框不允许输入
                # 不存在的文件名，用户就没法指定一个新文件去创建
                dialog = (filedialog.asksaveasfilename if want_create
                          else filedialog.askopenfilename)
                path = dialog(
                    title=title,
                    filetypes=filetypes if filetypes is not None else (),
                    initialdir=self._dialog_initialdir(initialdir),
                    defaultextension=self._default_extension(filetypes) if want_create else "",
                )
                if path:
                    # 与点击【选择】按钮保持同样的行为：回填、按需创建、触发回调
                    self._accept_path(path, auto_create=want_create)
                result["path"] = path or ""
            except tk.TclError:
                result["path"] = ""  # 窗口已销毁，按"没选文件"处理
            except Exception:  # noqa: BLE001 - 对话框内部出错也不能把调用方卡死
                result["path"] = ""
            finally:
                result["done"].set()
            return result["path"]

        if threading.current_thread() is threading.main_thread():
            # 本来就是主线程：直接弹对话框就行。
            # 这里绝不能走下面的 after + wait —— 主线程一 wait 就没法处理消息循环，
            # 排好的对话框回调永远不会执行，会直接卡死。
            return show_dialog()

        # 子线程：把对话框投递到主线程执行，本线程阻塞等待结果
        try:
            self.root.after(0, show_dialog)
        except (tk.TclError, RuntimeError):
            # 窗口已销毁，或者主线程没在跑消息循环（mainloop 未启动）：
            # 这两种情况都弹不出对话框，直接按"没选文件"返回，不抛异常给子线程
            return ""

        if not result["done"].wait(timeout):
            return ""  # 等超时：返回空串，调用方按"没选文件"处理即可
        return result["path"]

    def _dialog_initialdir(self, initialdir: Optional[str]):
        """
        【内部方法】决定对话框打开时定位到哪个目录。

        优先用调用方传进来的 initialdir；没传就用输入框里当前文件所在目录；
        都没有就返回 None（交给系统记住上次打开的位置）。
        """
        if initialdir:
            return initialdir
        current = self.var.get().strip()
        if not current:
            return None
        try:
            parent = Path(current).parent
        except (ValueError, OSError):
            return None  # 输入框里的内容不是合法路径，交给系统决定
        # Path("abc.txt").parent 是 "."，这种没有实际意义的目录直接不用
        return str(parent) if str(parent) not in ("", ".") else None

    def get_path(self) -> str:
        """获取当前文件路径字符串"""
        return self.var.get()

    def set_path(self, path: str):
        """手动设置文件路径"""
        self.var.set(path)

    @property
    def native_entry(self):
        """底层原生Entry输入框，用于自定义字体颜色等"""
        return self.entry


class MyButton(tk.Frame):
    """
    按钮控件，适配统一.add()接口
    参数：
        master:父容器
        text:按钮显示文字
        on_click:点击回调函数，无参数
    属性：
        .native_widget：底层原生tk.Button对象
    """
    def __init__(self, master, text: str, on_click=None,** kwargs):
        super().__init__(master, **kwargs)
        self.on_click = on_click
        self.btn = tk.Button(self, text=text, command=self._click)
        self.btn.pack(fill=tk.BOTH, expand=True)

    def _click(self):
        """内部点击事件，用户不要直接调用"""
        if self.on_click is not None:
            self.on_click()

    @property
    def native_widget(self):
        """底层原生Button，可修改颜色、字体等原生属性"""
        return self.btn


class HSplitFrame(tk.Frame):
    """
    水平左右分栏容器，提供 .left / .right 两个子容器
    参数：
        master:父容器
        left_weight:左侧区域拉伸权重，默认1
        right_weight:右侧区域拉伸权重，默认3
        proportional:是否严格按权重比例分配宽度，默认True。
                     True（默认）：左右宽度严格等于权重之比，窗口缩放比例不变，
                     并且两块**无缝拼接**，容器空间被完全用满；
                     False：左侧保持控件自然宽度（适合放文件选择框这类
                     固定宽度控件），窗口变大时多余宽度按权重分给右侧。
        gap:左右两块之间的间隙像素，默认0=无缝拼接。
    属性：
        .left：左侧子容器（_BoxFrame类型，支持.add()）
        .right：右侧子容器（_BoxFrame类型，支持.add()）
    方法：
        set_weights(left_weight, right_weight)：运行时改比例，立即重新布局
    """
    # 复合控件标记：被 add() 添加时自动铺满所在格子（见 _is_filling）
    _mytkui_composite = True

    def __init__(self, master, left_weight: int = 1, right_weight: int = 3,
                 proportional: bool = True, gap: int = _DEFAULT_SPLIT_GAP, **kwargs):
        super().__init__(master, **kwargs)
        self.root = self.winfo_toplevel()
        # 关闭尺寸传递：容器的大小由父容器（或主窗口加法）决定
        self.pack_propagate(False)
        self.grid_propagate(False)

        self.gap = max(0, int(gap))
        self._horizontal = True
        self.proportional = proportional
        # 先建单元格（比例模式由分栏决定格子大小，子控件需铺满格子），
        # 再设权重；set_weights 内部会立即布局
        self._left = _BoxFrame(self)
        self._right = _BoxFrame(self)
        # 位置和尺寸全部由 _layout_split 用 place 精确摆放（不用 grid：
        # grid 会先满足控件自然尺寸，权重只对增量生效，比例会被带偏）
        self._cells = (self._left, self._right)
        self.set_weights(left_weight, right_weight)  # 内部会立即布局，需先设好上面的属性
        self._sync_requested_size()  # 上报初始请求尺寸，父容器首次布局才分得到空间
        # 容器尺寸一变就重新切分；单元格内部变化冒泡上来也会走到这里
        self.bind("<Configure>", self._relayout)

    def set_weights(self, left_weight: int, right_weight: int):
        """设置左右权重并立即重新布局"""
        self.left_weight = max(0, left_weight)
        self.right_weight = max(0, right_weight)
        self.weights = (self.left_weight, self.right_weight)
        self._relayout()

    def set_gap(self, gap: int):
        """
        设置左右两块之间的间隙并立即重新布局。

        参数：
            gap: 间隙像素；0 表示无缝拼接（默认）
        """
        self.gap = max(0, int(gap))
        self._relayout()

    def _relayout(self, event=None):
        """
        【内部方法】重新切分两个单元格（Configure 回调，两种模式统一入口）。

        注意这里有两次布局：
            第 1 次按当前容器尺寸切分 → 控件铺满后，单元格自然尺寸随之变化；
            第 2 次在把新尺寸上报给父容器之后重算一遍，消除"按旧尺寸取整"
            留下的 1 像素偏差，让比例在任何窗口尺寸下都最接近权重之比。
        """
        _layout_split(self, self._cells, self.weights, self._horizontal, self.gap,
                      self.proportional)
        self._sync_requested_size()
        _layout_split(self, self._cells, self.weights, self._horizontal, self.gap,
                      self.proportional)

    def _sync_requested_size(self):
        """
        【内部方法】把本容器的请求尺寸设为"两个单元格自然尺寸之和 + 间隙"。

        为什么要这么做：
            padx/pady 一律为 0、单元格又是用 place 摆的，
            所以容器自身没有任何尺寸来源，不主动上报就只能按 1×1 参与父容器布局，
            被放进主窗口或另一个分栏时会直接塌成一条线。
        """
        w = self._left._natural_size("w") + self._right._natural_size("w") + self.gap
        h = max(self._left._natural_size("h"), self._right._natural_size("h"))
        self.config(width=max(1, w), height=max(1, h))

    @property
    def left(self) -> _BoxFrame:
        return self._left

    @property
    def right(self) -> _BoxFrame:
        return self._right


class VSplitFrame(tk.Frame):
    """
    垂直上下分栏容器，提供 .top / .bottom 两个子容器
    参数：
        master:父容器
        top_weight:上方区域高度权重，默认3
        bottom_weight:下方区域高度权重，默认1
        proportional:是否严格按权重比例分配高度，默认True。
                     True（默认）：上下高度严格等于权重之比（默认3:1），
                     窗口最大化、缩放、字体缩放时比例都保持不变，
                     并且上下两块**无缝拼接**，中间不会留下空隙；
                     False：先满足上下两块的自然高度，剩余空间再按权重分。
        gap:上下两块之间的间隙像素，默认0=无缝拼接。
    属性：
        .top：上方子容器（_BoxFrame类型，支持.add()）
        .bottom：下方子容器（_BoxFrame类型，支持.add()）
    方法：
        set_weights(top_weight, bottom_weight)：运行时改比例，立即重新布局
    """
    # 复合控件标记：被 add() 添加时自动铺满所在格子（见 _is_filling）
    _mytkui_composite = True

    def __init__(self, master, top_weight: int = 3, bottom_weight: int = 1,
                 proportional: bool = True, gap: int = _DEFAULT_SPLIT_GAP, **kwargs):
        super().__init__(master, **kwargs)
        self.root = self.winfo_toplevel()
        # 关闭尺寸传递：容器的大小由父容器（或主窗口加法）决定
        self.pack_propagate(False)
        self.grid_propagate(False)

        self.gap = max(0, int(gap))
        self._horizontal = False
        self.proportional = proportional
        # 先建单元格（比例模式由分栏决定格子大小，子控件需铺满格子），
        # 再设权重；set_weights 内部会立即布局
        self._top = _BoxFrame(self)
        self._bottom = _BoxFrame(self)
        # 位置和尺寸全部由 _layout_split 用 place 精确摆放（不用 grid：
        # grid 会先满足控件自然尺寸，权重只对增量生效，比例会被带偏）
        self._cells = (self._top, self._bottom)
        self.set_weights(top_weight, bottom_weight)  # 内部会立即布局，需先设好上面的属性
        self._sync_requested_size()  # 上报初始请求尺寸，父容器首次布局才分得到空间
        # 容器尺寸一变就重新切分，保证任何窗口尺寸下上下比例都严格等于权重之比
        self.bind("<Configure>", self._relayout)

    def set_weights(self, top_weight: int, bottom_weight: int):
        """设置上下权重并立即重新布局"""
        self.top_weight = max(0, top_weight)
        self.bottom_weight = max(0, bottom_weight)
        self.weights = (self.top_weight, self.bottom_weight)
        self._relayout()

    def set_gap(self, gap: int):
        """
        设置上下两块之间的间隙并立即重新布局。

        参数：
            gap: 间隙像素；0 表示无缝拼接（默认）
        """
        self.gap = max(0, int(gap))
        self._relayout()

    def _relayout(self, event=None):
        """
        【内部方法】重新切分两个单元格（Configure 回调，两种模式统一入口）。

        注意这里有两次布局：
            第 1 次按当前容器尺寸切分 → 控件铺满后，单元格自然尺寸随之变化；
            第 2 次在把新尺寸上报给父容器之后重算一遍，消除"按旧尺寸取整"
            留下的 1 像素偏差，让上下比例在任何窗口尺寸下都最接近权重之比。
        """
        _layout_split(self, self._cells, self.weights, self._horizontal, self.gap,
                      self.proportional)
        self._sync_requested_size()
        _layout_split(self, self._cells, self.weights, self._horizontal, self.gap,
                      self.proportional)

    def _sync_requested_size(self):
        """
        【内部方法】把本容器的请求尺寸设为"两个单元格自然尺寸之和 + 间隙"。

        为什么要这么做：
            padx/pady 一律为 0、单元格又是用 place 摆的，
            所以容器自身没有任何尺寸来源，不主动上报就只能按 1×1 参与父容器布局，
            被放进主窗口或另一个分栏时会直接塌成一条线。
        """
        h = self._top._natural_size("h") + self._bottom._natural_size("h") + self.gap
        w = max(self._top._natural_size("w"), self._bottom._natural_size("w"))
        self.config(width=max(1, w), height=max(1, h))

    @property
    def top(self) -> _BoxFrame:
        return self._top

    @property
    def bottom(self) -> _BoxFrame:
        return self._bottom


class AppWindow:
    """
    顶层主窗口类，程序入口窗口
    参数：
        title:窗口标题
        width:初始宽度
        height:初始高度
        min_w:窗口最小宽度，不能缩得更小
        min_h:窗口最小高度，不能缩得更小
    成员：
        .on_close：关闭窗口回调函数，返回False则阻止窗口关闭
    方法：
        add(widget, expand=False)：向主窗口添加一级控件
        说明：全部控件都是 expand=False 时，第一个控件自动占据全部剩余空间。
              否则主容器只能按请求尺寸摆放，窗口拖大后容器不跟着长大，
              分栏比例看着就会"怪怪的"。
        mainloop()：启动UI消息循环，放在代码最后一行
    """
    def __init__(self, title: str, width: int = 700, height: int = 400, min_w: int = 400, min_h: int = 250):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(min_w, min_h)

        self.root.grid_columnconfigure(0, weight=1)
        self._row_idx = 0
        self._first_widget: Optional[tk.Widget] = None  # 第一个一级控件，见 add()
        self.on_close: Optional[Callable[[], bool]] = None
        self.root.protocol("WM_DELETE_WINDOW", self._handle_close)

    def add(self, widget: tk.Widget, expand: bool = False):
        """
        在主窗口纵向添加一级控件
        :param widget: 控件或者分栏容器
        :param expand: True=纵向拉伸填充；False=高度固定（取自身请求高度）
        """
        if self._first_widget is None:
            # 记住第一个控件：如果后面没有任何控件 expand=True，
            # 就由它独占剩余空间，主容器才不会被"按请求尺寸摆放"困住
            self._first_widget = widget
        weight = 1 if expand else 0
        self.root.grid_rowconfigure(self._row_idx, weight=weight)
        widget.grid(row=self._row_idx, column=0, sticky="nsew", padx=5, pady=5)
        self._row_idx += 1
        self.root.after_idle(self._apply_fill_fallback)

    def _apply_fill_fallback(self):
        """【内部方法】没有任何控件声明 expand=True 时，让第一个控件填满剩余空间"""
        try:
            weights = [int(self.root.grid_rowconfigure(i, "weight"))
                       for i in range(self._row_idx)]
        except tk.TclError:
            return  # 窗口已关闭
        if any(weights):
            return  # 已经有控件负责拉伸，不动用户的意思
        if self._first_widget is not None:
            self.root.grid_rowconfigure(0, weight=1)

    def _handle_close(self):
        """窗口关闭内部回调，用户不要直接调用"""
        if self.on_close is not None:
            ok = self.on_close()
            if not ok:
                return
        self.root.destroy()

    def mainloop(self):
        """启动UI，放在程序末尾"""
        self.root.mainloop()


# ==================== 演示代码（运行本文件直接打开示例窗口） ====================
if __name__ == "__main__":
    import os

    win = AppWindow("MyTkUI Demo", 720, 450, 600, 300)
    # 一级：左右分栏容器
    hsplit = HSplitFrame(win.root)
    win.add(hsplit, expand=True)

    # 左侧面板：文件选择控件
    fs = FileSelect(hsplit.left, label="目标文件：")
    hsplit.left.add(fs)

    # 右侧面板：嵌套上下分栏容器
    vsplit = VSplitFrame(hsplit.right)
    hsplit.right.add(vsplit, expand=True)

    # 上区域：代码编辑器文本面板，初始化设置字体和颜色
    editor = LogPanel(vsplit.top, font_name="Consolas", font_size=11, fg="#EEEEEE", bg="#222222")
    vsplit.top.add(editor, expand=True)
    editor.info("编辑器就绪，Ctrl+S保存，Ctrl+滚轮缩放字体")
    # 绑定Ctrl+S保存回调
    def save_action():
        path = fs.get_path()
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(editor.get_all_text())
            editor.info(f"文件已保存: {path}")
        else:
            editor.warn("未选择保存文件！")
    editor.on_save = save_action

    # 下区域：日志输出面板
    log = LogPanel(vsplit.bottom, font_name="Consolas", font_size=10, fg="black", bg="#f8f8f8")
    vsplit.bottom.add(log, expand=True)
    log.info("日志面板就绪")

    # 文件选中回调函数
    def on_file(path):
        log.info(f"加载文件：{path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                editor.set_text(f.read())
        except Exception as e:
            log.error(f"读取失败：{e}")
    fs.on_select = on_file

    win.mainloop()
