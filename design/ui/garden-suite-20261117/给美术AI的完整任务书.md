# BlockOut 独立 UI 素材生成任务书

你是一名游戏 UI 美术资源制作员。请完整阅读本文件，严格按顺序生成素材。**只生成一个文件一个独立模块，不生成整页设计图，不生成多组件素材表，不生成需要开发者再次切图的图片。** 不修改代码或 Unity 工程。

## 一、输入与输出：先确认能读取文件

工作包绝对路径：

`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117`

必须首先打开这张图片，作为全部素材的唯一美术风格参考：

`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/input/style-reference.jpg`

这张图决定奶油厚边、玩具质感、花园世界、绿色按钮、光照和色彩。它只是风格输入，**禁止把参考截图中的矩形区域直接裁下来充当独立素材**，因为里面有背景残片、固定文字和数字。

如果你不能读取本地路径，明确告诉发起者需要上传 `style-reference.jpg` 作为附件。未看到图片前不要生成，更不要声称已读取。不要从互联网寻找另一张参考替代。

所有输出放在：

`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/`

下面每项都给出准确绝对路径。若你无法直接写本机文件，逐个提供准确命名的 PNG 下载，或者提供保留 `output/backgrounds`、`output/components`、`output/icons`、`output/optional` 目录结构的 ZIP，供发起者解压到工作包。不要声称已保存到你无法访问的电脑。

## 二、交付形式与不可违反的规则

1. **一张 PNG 只包含一个模块。** 一个按钮、一张底板、一个图标分别独立。不能把同类素材拼一排，也不能画整个弹窗再要求开发者切。
2. **不做整页设计图。** 需要背景时只画背景，需要按钮时只画空白按钮。各模块将直接用于 Unity 拼装真实界面。
3. 只有两个背景是全画幅不透明图。其余全部是 RGBA PNG，外部背景真实透明。不要用白底、灰底、棋盘格图案冒充透明。
4. 如果生成工具不支持透明，先报告限制，保留原图，提供标明 `needs-cutout` 的待处理源文件；不可假装透明素材已经完成。去背景不能抠掉奶油色描边或柔影，禁止粗暴按白色阈值抠图。
5. **所有底板、按钮、关卡块上无文字、无数字、无图标。** 只有明确要求的独立图标素材可以画对应符号。参考中的 37、36、38、39、40、3 和所有中文都不能烘焙进素材。
6. 单体正视，避免斜透视。材质统一：温暖奶油厚边、细暖金边、圆润倒角、柔和左上光源、下方短软阴影。像精致休闲游戏玩具，不是网页扁平图标、写实金属或镜面糖果。
7. 主绿色：柔和草绿到翠绿；奶油中心偏暖白；边缘浅金；危险色为珊瑚橙红；锁定为暖灰。不要使用粗黑线、强发光、霓虹、彩虹渐变或大片白色镜面高光。
8. 主体和阴影全部在画布内，外面保留透明边距，不能裁边。相同系列保持画布、主体位置、轮廓、圆角、光源与阴影一致，不能每张重新设计几何形状。
9. 按要求交付精确尺寸。模型不能直接输出时，可保持比例缩放并透明补边，不能拉伸；保留原图并在交付说明写清处理方式。背景可保持比例裁切到要求尺寸，但不能切掉重要内容。
10. 不覆盖输入，不改工程文件，不放入 Assets。已有候选修订先保存 `_v02`、`_v03`，选定后才复制成标准文件名。

## 三、数量与顺序

必做 **25 张独立 PNG**：2 张背景、11 张组件、12 张图标；另有 1 张可选角色。没有整页设计稿。

先生成四个母版：A01 花园背景、A03 奶油面板、A04 绿色按钮、A14 灯泡图标。打开检查是否与参考同风格；交给发起者确认后再继续其余素材。后续每项必须读取列出的母版，不依赖记忆。母版文件未生成或未选定，先停止依赖它的任务。

第一轮四张母版均只读取：

`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/input/style-reference.jpg`

后面每项都遵守第二节规则；每次生成都附上同一张主参考。增加母版时，主参考负责风格、母版负责几何与一致性，不把母版内容粘到一起。

## 四、背景：没有按钮、文字或任何 UI

### A01 · garden-home.png · 背景母版

读取：主参考 `input/style-reference.jpg`。

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/backgrounds/garden-home.png`

尺寸：1080×1920，竖版、不透明 PNG。

提示词：

> 根据参考的花园画廊世界，只画一张干净背景插画。晴朗蓝天、柔软白云、暖阳、左侧暖米色石质画廊外墙，右下方木画架展示无文字的花朵像素画，底部两侧柔软花草，中间温暖石质小径。画面精致、圆润、明亮，与参考相同的柔和立体插画风格。建筑主体限制在左侧约 25%，画架在右下方约 25%。中央 x=260..820、y=180..1570 保持空旷和低细节，供程序放关卡路径；顶部约 15% 为干净天空。不要画轨道、浮空平台、按钮、方块角色、数字、文字、UI 面板、门票、金币、导航条、水印和手机边框。不能直接擦参考数字而残留按钮，必须交付只有环境的完整背景。

### A02 · garden-play.png

读取：主参考，以及母版：

`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/backgrounds/garden-home.png`

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/backgrounds/garden-play.png`

尺寸：1080×1920，不透明 PNG。

提示词：

> 生成同一个花园世界供对局使用的安静背景，沿用背景母版的天空颜色、柔光方向、建筑和植物材质。中央 x=90..990、y=260..1560 是低对比、低细节、近似浅暖米色的自然散焦区域，之后会放真实棋盘。花草、天空和画廊只在外缘露出，不抢视线。中心与外围自然柔和过渡，不能画一个硬边矩形。不要画棋盘、棋盘托盘、箭头方块、数字、按钮、圆角面板、状态栏、道具、文字。这个文件只是背景，完整游戏界面会由程序叠加。

## 五、独立组件：无文字，真实透明

### A03 · panel-cream.png · 面板母版

读取：主参考。

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/panel-cream.png`

尺寸：768×1024，透明 PNG。

提示词：

> 一个独立、空白、正视的竖向圆角矩形奶油面板。暖金外缘、奶油厚内缘，圆润倒角，浅暖白平整中心，柔和左上光、短软下阴影，材料参考图片底部导航的奶油厚边。主体约 x=24..744、y=20..992，包含阴影不出画布。外面真实透明，中心是不透明浅暖白。四边装饰只能在距画布边缘 96 像素以内，中间 x=96..672、y=96..928 必须平整、颜色均匀、无纹理无图案，供九宫格拉伸。上、下边的中间段应平直；左、右边的中间段也平直。不要画文字、图标、按钮、横幅、铆钉、木纹、花草、接缝或辅助线。只生成一张面板，不生成整张弹窗。

九宫格建议边距 `[左96, 上96, 右96, 下96]`，只记录参数，不画到图里。实际导入前由开发者复核边缘与拉伸区。

### A04 · button-green.png · 按钮母版

读取：主参考。

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/button-green.png`

尺寸：768×256，透明 PNG。

提示词：

> 只画一个横向空白主按钮，参考绿色开始按钮的圆润厚度和材质。奶油厚外框、细暖金边、内层上半部草绿到下半部翠绿的柔和纵向渐变，下方略深绿色表示厚度，左上柔光，完整短软阴影。正视，主体约 x=16..752、y=12..232，圆角约 64 像素。左右各 96 像素容纳端部圆角，中间可横向拉伸；顶部和底部的中间段平直、材质均匀，不要横向光斑。外围真实透明。没有字、数字、右箭头、加号、星星、图标、花纹、粒子和背景。不是整屏按钮截图。只交一个按钮。

九宫格建议 `[96,56,96,56]`，后续主要横向拉伸，不能把边距线画出来。

### A05 · button-cream.png

读取：主参考和 `E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/button-green.png`。

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/button-cream.png`

尺寸：768×256，透明 PNG。

提示词：

> 基于按钮母版编辑，只把绿色内层改为温暖奶油米白，底部厚度改为浅蜂蜜色。画布、主体位置、轮廓、圆角、奶油外框、阴影和透明边距全部与母版相同，不重新设计形状。无文字无图标。交付一个独立空白奶油按钮，九宫格边距建议与母版相同。

### A06 · button-coral.png

读取：主参考和 `E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/button-green.png`。

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/button-coral.png`

尺寸：768×256，透明 PNG。

提示词：

> 基于按钮母版编辑，仅把内层变成柔和珊瑚橙红色，下方稍深表示厚度；奶油外框保持相同。画布、轮廓、圆角、光源、阴影和位置不变。不要画文字、骷髅、警告符号、图标或背景。只交付一个空白珊瑚按钮，九宫格边距建议与母版相同。

### A07 · round-base.png

读取：主参考，以及 `E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/panel-cream.png`。

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/round-base.png`

尺寸：256×256，透明 PNG。

提示词：

> 一个独立空白圆形奶油按钮底座，同面板母版的奶油与暖金双层边缘，圆润略凸暖白中心，左上柔光、下方短软阴影。正视圆形，不是椭圆。圆心约 (128,120)，主体直径约 208 像素，阴影完整留在画布内。没有齿轮、加号、暂停线、数字、文字、图标和其他小按钮。中心不透明，外部真实透明。

### A08 · tile-green.png · 关卡节点母版

读取：主参考和 `E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/button-green.png`。

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/tile-green.png`

尺寸：320×352，透明 PNG。

提示词：

> 一个独立空白、近正方形的圆角绿色关卡节点，参考当前关卡 37 的绿色饱满表面与奶油厚外框，但绝不画 37。材料与绿色按钮母版相同。正视，主体约 x=20..300、y=16..312，下方保留柔影空间。无数字、文字、箭头、角色、轨道、气泡、下方三角、光环、星标或锁。绿色内面完整平滑，不留下擦除数字的痕迹。

### A09 · tile-grey.png

读取：主参考和 `E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/tile-green.png`。

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/tile-grey.png`

尺寸：320×352，透明 PNG。

提示词：

> 只编辑关卡节点母版的面层颜色为暖灰，保留同一奶油外框、形状、位置、圆角、厚度和阴影。表示未解锁状态。不要画锁，锁是另一个独立图标；不要画数字、文字、徽标、光环或背景。

### A10 · tile-purple.png

读取：主参考和 `E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/tile-green.png`。

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/tile-purple.png`

尺寸：320×352，透明 PNG。

提示词：

> 只编辑关卡节点母版的面层为柔和紫色。画布、轮廓、位置、奶油外框、厚度、阴影不变。不要画数字、星标、锁、文字、光环或背景。只要一个独立空白紫色节点。

### A11 · frame-art.png

读取：主参考和 `E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/panel-cream.png`。

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/frame-art.png`

尺寸：768×768，透明 PNG。

提示词：

> 一个独立正视方形像素画展示框。奶油厚框、细暖金内缘、圆润外角，材料与奶油面板母版相同。中央 x=96..672、y=96..672 必须完全透明，方便程序放入每关不同的真实图片；外部也透明。只画四边相框及柔影，不画任何图片、白色背板、玻璃、反光、文字、花草、星星或按钮。框完整，不裁边。

九宫格建议 `[96,96,96,96]`，实际以透明开口复核；不要把开口填成白色。

### A12 · ribbon-coral.png

读取：主参考和 `E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/button-coral.png`。

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/ribbon-coral.png`

尺寸：768×256，透明 PNG。

提示词：

> 一个独立正视空白珊瑚色庆祝横幅，柔软圆润的中间带面，两侧有短折带，奶油暖光、较深珊瑚折面，和珊瑚按钮同色系。中间 x=160..608、y=60..184 保持干净，程序会叠加通关文字。不画文字、奖杯、星星、彩纸、人物、金币或背景，所有折带与阴影留在画布内。

### A13 · pill-cream.png

读取：主参考和 `E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/panel-cream.png`。

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/pill-cream.png`

尺寸：512×160，透明 PNG。

提示词：

> 一个独立空白横向奶油胶囊底板，用于金币栏或简短提示。奶油厚边、细暖金边、平整暖白中心，材质与面板母版相同。主体约 x=12..500、y=10..142，两端半圆，正视，短软下阴影。没有金币、门票、加号、数字、文字、图标、进度填充和背景。左右各 80 像素保留端部，中间可横向拉伸。不要做成绿色按钮。

九宫格建议 `[80,40,80,40]`，主要横向拉伸。

## 六、独立图标

以下 A14～A25 **每项各生成一个 256×256 透明 PNG**。不是生成一张包含 12 个图标的大图。

每个图标都读取主参考。除 A14 外，还必须读取图标母版：

`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-hint.png`

共同提示词，必须与每项描述一起使用：

> 单个独立游戏图标，真实透明背景，材质、光源、饱满程度与图标母版一致。柔和左上光、圆润造型、精简细节、短柔影。主体居中，最长边约 196～216 像素，至少 20 像素透明边距，阴影完整。缩小到 32×32 像素仍能辨认。不要按钮底座、圆形徽章、装饰背景、文字、数字、边框、散落粒子和长投影。不把其他图标一起画入文件。

### A14 · icon-hint.png · 图标母版

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-hint.png`

具体提示词：一个金黄色灯泡，温暖奶油光的灯泡玻璃，浅金短底座，轮廓圆润厚实。灯泡本身完整，不画外部发光射线或光晕，不放在圆形底板上。

### A15 · icon-hammer.png

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-hammer.png`

具体提示词：一把玩具木锤，短蜂蜜色手柄、圆润橙金锤头，整体朝右上倾斜约 30 度。轮廓清楚，一眼能认出锤子，不画钉子、敲击特效、木板和第二个锤子。

### A16 · icon-magic.png

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-magic.png`

具体提示词：一根绿色短柄魔法棒，顶端连接一颗金色五角星，整体朝右上倾斜约 30 度。不要炸弹、引线、爆炸、漂浮星点和外部光圈。五角星与棒柄是同一个完整道具。

### A17 · icon-settings.png

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-settings.png`

具体提示词：一个正视暖灰咖色齿轮，中心清楚的圆孔，8 个圆润厚实齿。没有底座、按钮圆框、内嵌数字或其他符号；中央孔为透明。

### A18 · icon-home.png

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-home.png`

具体提示词：一座小巧奶油房子，珊瑚红圆润屋顶，浅蓝色门，正面或极轻微立体感。只画一栋房子，没有院子、地面、植物、文字和后面的建筑。

### A19 · icon-levels.png

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-levels.png`

具体提示词：一幅小型金色木画框，里面简单蓝天、绿色小山和金色太阳，图画完全在框内，外面透明。它是导航图标，不是 A11 空白大画框，不要数字或字。

### A20 · icon-store.png

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-store.png`

具体提示词：一个小巧奶油道具篮，里面露出一枚金灯泡和一把短柄木锤，合成一个清晰的道具商店图标。不要调色板、衣服、皮肤、价格和文字。小尺寸仍以篮子轮廓为主，不堆很多物品。

### A21 · icon-coin.png

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-coin.png`

具体提示词：一枚正视圆形金色金币，有厚边和中央低浮雕五角星，柔和光泽。只画一枚，不画一堆金币，不画货币字母、数字、价格、加号或外部光芒。

### A22 · icon-heart.png

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-heart.png`

具体提示词：一颗完整珊瑚红爱心，圆润饱满，轻微可见侧面厚度和柔和高光。没有脸、翅膀、箭头、光芒、数字或外框。

### A23 · icon-heart-broken.png

额外必须读取：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-heart.png`

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-heart-broken.png`

具体提示词：编辑完整爱心母版，保持原有画布、外轮廓、位置、材质和光线，只在中央增加一条清楚窄锯齿裂缝，裂缝透明。左右两半仍组成可辨认的爱心。不要碎成很多片，不画碎屑、眼泪或文字。

### A24 · icon-lock.png

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-lock.png`

具体提示词：一个小暖灰色挂锁，奶油浅色锁梁、圆润锁身、清楚小钥匙孔，正视。只有挂锁，没有圆形底板、关卡节点、数字、文字、链条或钥匙。

### A25 · icon-trophy.png

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/icons/icon-trophy.png`

具体提示词：一个金色小奖杯，双耳、杯身中央五角星浅浮雕、珊瑚色短底座。整体完整。没有字、奖牌、月桂、丝带、彩纸和背景。用于通关装饰，不代表新增成就功能。

## 七、可选角色：最后做，不阻塞正式界面

### A26 · mascot.png

读取：主参考和 `E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/components/tile-green.png`，后者只参考材料，角色颜色仍是黄色。

保存到：`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/optional/mascot.png`

尺寸：512×640，透明 PNG。

提示词：

> 一个独立黄色圆角方块角色，参考原图路径底部的小方块。温暖深咖大眼睛、小微笑、柔和黄色厚实身体，脸下方有一个绿色向右箭头浮雕。可爱但简洁，不加四肢。主体居中，至少 32 像素透明边距。不画地面、轨道、光环、漂浮方块、数字、按钮、文字或旁边的角色。只作为首页装饰，不能把它放到真实棋盘上。

## 八、不需要生成的东西

- 不生成棋盘和异形箭头方块贴图：已有规则正确的素材，不能让 AI 改变占格与箭头。
- 不生成中文、关卡数字、数量、价格、百分比、奖励：这些由 Unity 动态显示。
- 不生成返回箭头、加号、关闭叉、暂停双竖线和勾选：简单几何由程序统一处理。
- 不生成关卡道路、进度条填充：由程序绘制并绑定实际进度。
- 不生成完整设置、失败、暂停、商店页面：复用独立面板、按钮和图标即可。
- 不生成按钮按下、禁用等独立形状：由程序用同一素材处理明暗、缩放和位移，避免变形跳动。
- 不生成“每日、任务、成就、皮肤”的入口文字和整页：这些不是现有已实现玩法，不做假入口。

## 九、这些模块如何组成完整界面（无需你另画整页）

| 页面 | 使用素材 | 程序负责的内容 |
|---|---|---|
| 加载 | garden-home、panel-cream | 游戏名、加载进度 |
| 首页 | garden-home、关卡节点、绿色按钮、圆底、金币与导航图标 | 当前关号、路径、解锁、开始/继续、金币、导航 |
| 游戏 | garden-play、panel-cream、round-base、三个工具图标、心 | 棋盘、暂停、计时、心数、进度、道具数量 |
| 关卡 | garden-home、panel-cream、关卡节点、锁 | 章节、可玩状态、关号、滚动与重玩 |
| 道具 | garden-home、panel-cream、按钮、工具图标、金币 | 价格、数量、解锁条件、购买 |
| 结算 | garden-home、frame-art、ribbon-coral、trophy、按钮、金币 | 真实完成图片、奖励、下一关、保存重试 |
| 暂停/设置/确认/关于/引导 | panel-cream、按钮、round-base | 实际文案、开关、确认和返回 |
| 失败 | panel-cream、heart-broken、按钮 | 原因、复活条件、重试 |
| 提示与状态 | pill-cream、lock、coin | 提示、数量不足、锁定说明 |

## 十、交付检查：必须逐项诚实回答

1. 25 张必做 PNG 是否分别交付，一个文件一个模块？缺哪些？
2. 每张实际尺寸是否符合要求？有没有只改文件名、没有改图片尺寸？
3. 除两个背景外，外部是否实际 alpha=0？有没有白底或假透明棋盘格？
4. 有没有固定文字、数字、背景残片、旁边的组件、水印？
5. 三种按钮与三种节点是否保持相同轮廓、位置和阴影？
6. 单体有没有裁边、黑边、白色杂边、抠坏的奶油外框？
7. 图标缩到 32×32 是否还能区分？魔法棒有没有被误画成炸弹？
8. 面板、按钮、胶囊拉伸区域是否干净？不要用花纹掩盖不合格素材。
9. frame-art 中央是否真实透明？没有烘焙样例画或白背板？
10. 不能满足的项目如实标记待修，不能只写“全部完成”。

最后生成文本说明：

`E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output/delivery.md`

内容包含：文件名、实际尺寸、透明情况、生成/编辑方式、使用了哪个母版、已知问题、未完成项。不具备写文件权限时与 PNG 一起提供下载。不要声称已经导入 Unity 或通过运行验收。
