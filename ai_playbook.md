# AI工具使用手册

## 1. 使用的AI工具
- 主要工具：ChatGPT 4o、Cursor，豆包，文心一言。

## 2. AI使用案例
### 实例1
- 提示词："你是一名资深unity开发，为我分析以下代码我点击鼠标右键，小鸟并未给出输出反馈的原因
```
using System.Collections;
using System.Collections.Generic;
using UnityEngine;


public class birdControl : MonoBehaviour
{
    
    public float force1 = 10f;
    //定义一个新刚体
    public Rigidbody2D rbody1;


    //use this for initialization;
    void Start()
    {
        //  获取小鸟得刚体
        rbody1 = GetComponent<Rigidbody2D>();

    }

    //Update is called once per frame;
    void Update()
    {
        //判断点击则给小鸟向上  0左，1右键，2鼠标中键
        if (Input.GetMouseButtonDown(1))
        {
            rbody1.velocity = new Vector2(0, force1);
        }
    }
}"
```

- AI输出：
```
- 作为资深Unity开发者，我会从**代码逻辑、组件配置、运行环境**三个核心维度，逐一拆解你点击鼠标右键小鸟无反馈的原因，每个原因都对应可落地的排查方法，新手也能一步步验证：

### 一、先明确核心结论
你的代码本身语法无错误，但小鸟无反馈是**“输入检测+物理组件+运行环境”** 三类问题的叠加，按优先级排序如下：

---

### 二、逐维度排查原因（附验证方法）
#### 维度1：输入检测的核心问题（最易踩坑）
你的代码用`Input.GetMouseButtonDown(1)`检测**鼠标右键**，但这个检测有3个隐形前提，任一不满足就无反馈：
1. **Game窗口未激活**（90%新手踩坑）
   - 原因：Unity的输入检测只对「激活的Game窗口」生效，若运行后点击了Scene窗口/其他软件，输入会被忽略；
   - 验证：运行游戏后，先点击Game窗口内的画面（让窗口高亮），再右键点击；
   - 补充：即使激活了窗口，若鼠标光标在Game窗口外（比如拖到编辑器边缘），右键也不会被检测。

2. **鼠标右键被其他软件抢占**
   - 原因：微信/QQ/录屏软件等会绑定鼠标右键快捷键，导致Unity接收不到右键输入；
   - 验证：关闭所有后台软件，只保留Unity，再测试右键。

3. **输入检测逻辑的“一次性”特性**
   - 原因：`GetMouseButtonDown(1)`仅在**右键按下的那1帧**触发，若长按右键/连续点击过快，可能因帧率问题漏检测；
   - 验证：替换为`Input.GetMouseButton(1)`（长按持续触发）测试：
     ```csharp
     if (Input.GetMouseButton(1)) // 替换原有的GetMouseButtonDown
     {
         Debug.Log("右键被按住了！"); // 加日志验证
         rbody1.velocity = new Vector2(0, force1);
     }
     ```

#### 维度2：物理组件（Rigidbody2D）配置错误（核心）
即使输入检测生效，若Rigidbody2D配置不对，小鸟也不会移动，且无任何报错：
1. **Rigidbody2D未启用/类型错误**
   - 必配项（缺一不可）：
     ✅ Body Type = `Dynamic`（动态刚体，才能受速度/重力影响）；
     ✅ Simulated = 勾选（取消则刚体完全失效）；
     ✅ Gravity Scale > 0（建议1~2，设为0则小鸟不会下落，也无跳跃反馈）；
   - 验证：运行游戏后，看小鸟是否会自然下落——若悬浮不动，就是Gravity Scale=0或Body Type错误。

2. **Rigidbody2D组件缺失/脚本未获取到**
   - 原因1：小鸟对象上根本没加Rigidbody2D组件，`rbody1 = GetComponent<Rigidbody2D>()`会返回`null`，执行`rbody1.velocity`时Unity会静默失败（无报错，但代码不生效）；
   - 原因2：手动在Inspector给`rbody1`赋值了空对象（覆盖了Start()的自动获取）；
   - 验证：在Start()加日志，检查刚体是否获取成功：
     ```csharp
     void Start()
     {
         rbody1 = GetComponent<Rigidbody2D>();
         if (rbody1 == null)
         {
             Debug.LogError("小鸟没有Rigidbody2D组件！"); // 无此日志=获取成功
         }
     }
     ```

#### 维度3：脚本/对象的基础配置问题（易忽略）
1. **脚本未正确挂载/启用**
   - 验证：运行游戏后，选中Hierarchy的Bird对象，看Inspector面板：
     ✅ `birdControl`脚本组件存在；
     ✅ 脚本组件左上角的勾选框为√（未勾选则脚本不运行）。

2. **小鸟对象位置异常（视觉上无反馈）**
   - 原因：小鸟可能在相机视野外（比如Position=(100,100,0)），即使移动了也看不到；
   - 验证：运行游戏时，在Scene窗口选中Bird对象，看其Transform.Position是否在相机视野内（正交相机Size=6时，建议Bird的Position=(0,0,0)）。

3. **force1数值过小（反馈不明显）**
   - 原因：`force1=10`看似合理，但如果相机Size过大（比如你之前的16.7），10单位的速度移动会被“缩放”得几乎看不见；
   - 验证：把`force1`调到50~100，再测试右键，看是否有明显移动。

---

### 三、一键验证的最简改造（快速定位问题）
把你的代码替换为以下版本，运行后按右键，通过Console日志直接定位问题：
```csharp
using UnityEngine;

public class birdControl : MonoBehaviour
{
    public float force1 = 50f; // 调大数值，增强反馈
    public Rigidbody2D rbody1;

    void Start()
    {
        // 1. 检查刚体是否获取成功
        rbody1 = GetComponent<Rigidbody2D>();
        if (rbody1 == null)
        {
            Debug.LogError("[错误] 小鸟缺少Rigidbody2D组件！");
            return;
        }
        Debug.Log("[成功] 刚体获取成功，Gravity Scale=" + rbody1.gravityScale);
    }

    void Update()
    {
        // 2. 检测右键输入并打印日志
        if (Input.GetMouseButtonDown(1))
        {
            Debug.Log("[输入] 鼠标右键被按下！");
            // 3. 强制设置速度，并打印速度值
            rbody1.velocity = new Vector2(0, force1);
            Debug.Log("[物理] 小鸟速度被设置为：" + rbody1.velocity);
        }
    }
}
```
```
#### 日志解读（快速定位）：
| 日志内容 | 问题定位 | 解决方法 |
|----------|----------|----------|
| 无任何日志 | 脚本未挂载/未启用 | 重新挂载脚本，勾选启用 |
| [错误] 小鸟缺少Rigidbody2D | 无刚体组件 | 给小鸟添加Rigidbody2D，设为Dynamic |
| [成功] 刚体获取成功 + 无[输入]日志 | Game窗口未激活/右键被抢占 | 激活Game窗口，关闭后台软件 |
| [输入]日志有 + [物理]日志有 + 小鸟不动 | 相机视野外/force1过小 | 调整小鸟位置，调大force1 |

---

### 总结（核心关键点）
1. **输入层**：优先激活Game窗口，这是新手无反馈的头号原因；
2. **物理层**：确保Rigidbody2D为Dynamic、Simulated勾选、Gravity Scale>0；
3. **调试层**：加日志是定位无反馈问题的最快方式，不要依赖“视觉判断”。

按上述步骤排查，99%能解决你的问题——如果仍无日志，大概率是Unity编辑器缓存问题，关闭Unity后删除项目的`Library`文件夹再重启即可。
```
- 验证方式：测试组件属性时发现Rigidbody2D和另一个碰撞检测属性冲突，调整后问题解决。

### 实例2
- 提示词："你是一名资深python后端开发，帮助我将下面代码中的参数检验部分使用Pydantic进行重写，并且为我讲解Pydantic的使用方法。（省略代码内容）“

- AI输出：
```
(省略部分代码内容)
# 一、重构后完整代码（Pydantic参数校验版）
首先我会把原有手动校验的`check_answers`函数替换为Pydantic的结构化校验，并保留所有核心业务逻辑，先看完整代码：


# 二、Pydantic核心语法讲解（结合本次重构）
Pydantic是Python中用于**数据验证和设置管理**的库，核心优势是：**结构化校验、自动类型转换、友好的错误提示、代码更简洁**，以下是本次用到的核心语法：

## 1. 基础：定义校验模型（BaseModel）

from pydantic import BaseModel

class AnswersModel(BaseModel):
    # 字段名: 类型 （未设默认值 = 必填字段）
    annual_invoice: float | int  # 联合类型：支持int或float
    annual_flow: float | int
    has_mortgage: bool
    overdue_level: str

- **核心规则**：
  - 继承`BaseModel`的类就是一个校验模型
  - 字段声明格式：`字段名: 类型`，未指定默认值则为**必填字段**（替代原有`required_fields`检查）
  - 支持Python原生类型（int/float/bool/str）、联合类型（`|`）、列表/字典等复杂类型

## 2. 自定义字段校验（field_validator）

from pydantic import field_validator

class AnswersModel(BaseModel):
    # ... 字段定义 ...

    # 单个/多个字段的自定义校验器
    @field_validator('annual_invoice', 'annual_flow')  # 校验多个字段
    def validate_non_negative(cls, v):  # cls=模型类，v=字段值
        if v < 0:
            raise ValueError(f"值必须是非负数，当前值：{v}")
        return v  # 校验通过必须返回值（可修改后返回）

    @field_validator('overdue_level')  # 校验单个字段
    def validate_overdue_level(cls, v):
        valid_values = ["none", "M1", "M3+"]
        if v not in valid_values:
            raise ValueError(f"必须是{valid_values}中的一个，当前值：{v}")
        return v

- **核心规则**：
  - 装饰器`@field_validator(字段名1, 字段名2...)`指定要校验的字段
  - 函数参数固定：`cls`（模型类本身）、`v`（当前字段的值）
  - 校验失败：抛出`ValueError`（Pydantic会自动捕获并封装）
  - 校验成功：必须返回值（可以是原数值，也可以是处理后的值，比如类型转换）

## 3. 模型实例化与校验

# 方式1：直接传参
model = AnswersModel(annual_invoice=300, annual_flow=600, has_mortgage=False, overdue_level="none")

# 方式2：解包字典（适配接口请求的JSON数据）
answers = request.get_json()
model = AnswersModel(**answers)  # **解包字典，自动按字段名匹配

- **核心行为**：
  - 实例化时自动执行所有校验（字段类型、自定义规则）
  - 校验失败会抛出`ValidationError`异常
  - 校验成功生成模型实例，可通过`model_dump()`转换为字典（兼容原有业务逻辑）

## 4. 错误处理（ValidationError）

from pydantic import ValidationError

try:
    validated_answers = AnswersModel(**answers)
except ValidationError as e:
    # e.errors() 返回错误列表，每个错误是字典：
    # [{'loc': ('annual_invoice',), 'msg': '值必须是非负数，当前值：-100', 'type': 'value_error'}]
    error_detail = e.errors()[0]
    error_msg = f"参数校验失败：{error_detail['loc'][0]} - {error_detail['msg']}"

- **错误字典核心字段**：
  - `loc`：错误字段的路径（元组），比如`('annual_invoice',)`表示该字段出错
  - `msg`：错误提示信息（自定义的ValueError内容）
  - `type`：错误类型（如value_error/type_error）

## 5. 模型实例的常用方法
| 方法 | 作用 | 示例 |
|------|------|------|
| `model_dump()` | 转换为字典（兼容原有业务逻辑） | `validated_answers.model_dump()` |
| `model_dump_json()` | 转换为JSON字符串 | `model.model_dump_json(ensure_ascii=False)` |
| `dict()`（旧版） | 同model_dump（Pydantic v1兼容） | `model.dict()` |

# 三、Pydantic vs 手动校验的优势
| 维度 | 手动校验（原有check_answers） | Pydantic校验 |
|------|--------------------------------|--------------|
| 代码量 | 20+行，需手动遍历字段、写if判断 | 10行左右，结构化声明 |
| 类型校验 | 需手动`isinstance`判断 | 自动校验，支持联合类型 |
| 错误提示 | 需手动拼接错误信息 | 自动生成结构化错误，可精准定位字段 |
| 可扩展性 | 新增字段需修改多个地方 | 仅需在模型中新增字段+校验器 |
| 维护成本 | 高（逻辑分散） | 低（逻辑集中在模型） |
| 生态兼容 | 无 | 兼容FastAPI、Django等框架，支持ORM模型映射 |

# 四、额外扩展（实用Pydantic语法）
## 1. 设置默认值（可选字段）

class AnswersModel(BaseModel):
    annual_invoice: float | int = 0.0  # 默认值=0.0，可选字段
    overdue_level: str = "none"  # 默认值="none"


## 2. 类型转换（自动）
Pydantic会自动尝试类型转换，比如：

# 传入字符串"300"，会自动转为int/float
model = AnswersModel(annual_invoice="300", annual_flow=600, has_mortgage=False, overdue_level="none")
print(model.annual_invoice)  # 输出：300.0（float类型）


## 3. 嵌套模型（复杂结构）
如果请求参数有嵌套结构，可定义嵌套模型：

class InterestRateModel(BaseModel):
    min: float
    max: float

class ProductModel(BaseModel):
    name: str
    interest_rate: InterestRateModel  # 嵌套模型

# 校验：自动校验嵌套结构
product = ProductModel(name="建行云税贷", interest_rate={"min":3.6, "max":8.0})


# 五、总结
本次重构核心是将原有“手动遍历+if判断”的校验逻辑，替换为Pydantic的**结构化模型校验**，核心改动点：
1. 定义`AnswersModel`替代`check_answers`函数，自动完成必填、类型、自定义规则校验；
2. 接口中通过`AnswersModel(**answers)`触发校验，捕获`ValidationError`并返回友好提示；
3. 用`model_dump()`转换为字典，保持原有业务逻辑完全兼容。

Pydantic的核心语法可总结为：**定义模型（BaseModel）→ 声明字段+类型 → 自定义校验器（field_validator）→ 实例化校验 → 处理错误**，掌握这一套流程，就能高效实现Python后端的参数校验。

```
- 验证方式：测试接口时，传入各种错误参数，均能正确捕获并返回对应的错误信息。

## 3. AI翻车记录
       
&emsp;AI幻觉问题，在写面向建筑热环境调控的室内人员检测与行为识别技术研究的项目申报书时，导师要求阅读相关文献并总结技术现状。使用AI生成的文献综述部分，发现引用的文献和数据均为虚构，且技术细节描述不准确。转而要求AI给出推荐文献，我去阅读时发现推荐的文献可能不存在，有的与主题不符或者是低质量的文章。最终只能依靠自己查找和阅读真实文献来完成。

## 4. 经验总结
- AI在编写一些简单逻辑代码，格式转化代码的效率和可行率较高，但在涉及复杂业务逻辑和核心规则设计时，AI生成的代码经常会出现一些问题，需要程序员进行后续的修改和完善。
- AI在编写文档时，容易出现虚构引用和数据的问题，必须进行严格的核实和验证。除了填表式的内容可以使用AI生成外，其他部分建议程序员自己编写。
- AI生成的代码必须经过手动测试，确保逻辑的正确。尽量想一些边界条件和异常情况进行测试，发现问题后再进行修改。