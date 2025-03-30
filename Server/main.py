#coding=utf-8
from openai import OpenAI
from socketplus import *
import re
import ast

client = OpenAI(
     api_key="a4693007f56d3fe4fc73df75681933527ddf5fe8",  # 含有 AI Studio 访问令牌的环境变量，https://aistudio.baidu.com/account/accessToken,
     base_url="https://aistudio.baidu.com/llm/lmapi/v3",  # aistudio 大模型 api 服务域名
)

systems = "假如你是一个科研导师，目前需要你来针对某个具体课题，根据需求，对不同的组员，安排去做不同的准备工作。组员是固定的，但是每次的任务不同。\
        员工们的姓名为：刘一、陈二、张三、李四 \
        一、角色的名称为“姓名”+“任务”如：张三查论文,李四写代码,等等，具体任务你可以根据任务要求进行实际设计，组员姓名就用这四位就可以，不得出现除刘一、陈二、张三、李四以外的名字。\
        二、每个角色的工作任务必须不重不漏，角色一次性生成完毕，要尽可能多一些，复杂一些，而且角色之间一定要有指名道姓的配合。\
        三、整体的输出以汇报形式开展，一次生成全部组员的，结束工作时，进度为100%。每个人的汇报除了描述做了什么，需要仅用表情符传达意思，分别是情绪表情符和表达事务意思的表情符。汇报一定要说清除每个人自己任务成果的详细内容。\
        四、你这个科研导师所在的学校，有机房、会议室、办公室、财务室、图书馆、实验室、自习室、算力中心、打印间九个地点，每个角色如果要做某个任务，一定必须要提一下去哪个地点。不得出现除上述房间名称以外的房间。不同的角色是可以去同一个地方的。\
        五、汇报需要按照如下的json格式回答，不能掺杂其他的文字，使用'''json'''来回答 \
		{  \
			'task':'任务', // string，意思是这个团队近期要准备的课题\
			'tasks':[\
			    {\
			        'name':'姓名', // string,意思是哪个组员\
			        'to':'地点', // string，该员工要去的地方(必须是上述所提到的房间)\
			        'do_':'事情', // string，该员工的任务（要做的事情，描述得尽可能详细）\
                    'content':'内容', // string，该员工的汇报（任务成果的详细内容，描述得尽可能详细）\
			        'emoji':'表情 表情'  // emoji unicode string，2个表情（其中不可以使用文字，且只要两个），分别表达情绪和工作类型\
			    },\
			    ……\
            ]\
		}\
        如：\
        {\
			'task':'解决图像光照不均匀问题', // string，意思是这个团队近期要准备的课题\
			'tasks':[\
			    {\
			        'name':'张三', // string,意思是是哪个组员\
		            'to':'档案室', // string，该组员要去的地方\
		            'do_':'查阅文献,翻译外文文献', // string，该组员的任务（要做的事情，描述得尽可能详细）\
                    'content':'《Adaptive Logarithmic Mapping For Displaying High Contrast Scenes》，提出了自适应对数映射方法，用于处理高动态范围图像的光照不均匀问题；《Retinex Theory for Image Enhancement》，Retinex理论的经典论文，为后续基于Retinex的算法奠定了基础；《A Multiscale Retinex for Bridging the Gap Between Color Images and the Human Observation of Scenes》多尺度Retinex算法，有效改善光照不均匀', // string，该员工的汇报（任务成果的详细内容，描述得尽可能详细）\
                    'emoji':'😀📕' ,// emoji unicode string，2个表情（其中不可以使用文字，且只要两个），分别表达情绪和工作类型 \
			    },\
		        ……\
		    ]\
		} \
         请你特别注意，不要生成过多的表情符号,也不要使用文字来代替表情符号！！！不要生成过多的表情符号,也不要使用文字来代替表情符号！！！"

messages = [
    {
        "role": "user",
        "content": systems
    },
    {
        "role": "assistant",
        "content": "请输入你的具体任务"
    }
]

json_block_regex = re.compile(r"```(.*?)```", re.DOTALL)
def extract_json(content):
    json_blocks = json_block_regex.findall(content)
    if json_blocks:
        full_json = "\n".join(json_blocks)
        if full_json.startswith("json"):
            full_json = full_json[5:]
        return full_json
    else:
        return None

def string_to_dict(dict_string):
    try:
        dictionary = ast.literal_eval(dict_string)
        return dictionary
    except (SyntaxError, ValueError) as e:
        print(f"转换字符串为字典时出错: {e}")
        return None

def replace_key(dictionary, old_key, new_key):
    if old_key in dictionary:
        dictionary[new_key] = dictionary[old_key]
        del dictionary[old_key]
    else:
        print(f"Key '{old_key}' not found in the dictionary.")

def percentage_to_number(s):
    no_percent = s.replace('%', '')
    return int(no_percent)

def to_number(s):
    return int(s)

def cheak(response):
    if response["process"] == 100:
        return True
    else:
        return False

def chat(message):
    if isinstance(message, str):
        message = {"role": "user", "content": message}
    messages.append(message)

    response = client.chat.completions.create(
        model="ernie-4.0-turbo-128k",
        messages = messages,
        top_p = 0.01,
    )
    #使用deepseek系列模型要去除输出的<think>
    result = response.choices[0].message.content

    messages.append(
        {
            "role": "assistant",
            "content": result,
        }
    )
    return result

def extract_info(json_str):
    try:
        if json_str["type"] == "question":
            return True,json_str["question"]
        if json_str["type"] == "response":
            return False,json_str["response"]
    except json.JSONDecodeError as e:
        return f"Error  JSON: {e}"


def remove_text_spaces_keep_emojis_v2(task_data):
    for task in task_data['tasks']:
        # Remove all alphabetic characters and spaces from the 'emoji' field
        task['emoji'] = ''.join(char for char in task['emoji'] if not char.isalpha() and not char.isspace())

    return task_data

def trim_emoji(tasks):
    for task in tasks:
        if len(task['emoji']) > 5:
            task['emoji'] = task['emoji'][:5]  # Keep only the first 5 characters
    return tasks

socketserver = socketclient('127.0.0.1',12339)

def main():
    try:
        recv_data = socketserver.recv()
    except Exception as e:
        print(f"接收数据错误: {e}")
        return
    is_new_task, task_content = extract_info(recv_data)

    enhanced_prompt = f"{task_content}\n请直接生成完整任务报告，要求：\n" \
                      "1. 包含所有4位组员的完整工作内容\n" \
                      "2. 进度直接设置为100%\n" \
                      "3. 使用统一的任务列表\n" \
                      "4. 确保每个组员都有详细的工作描述和正确的表情符号"

    response = chat(enhanced_prompt)

    json_str = extract_json(response)
    if not json_str:
        print("错误：未检测到有效的JSON数据")
        return

    task_data = string_to_dict(json_str)
    if not task_data:
        print("错误：JSON转换失败")
        return

    task_data["process"] = 100  # 覆盖进度为100%

    # 数据清洗
    task_data = remove_text_spaces_keep_emojis_v2(task_data)
    validated_data = {
        "resultType": "task",
        "closingReport": "",
        **task_data
    }

    # 发送任务数据
    try:
        socketserver.send(validated_data)
    except Exception as e:
        print(f"发送任务数据错误: {e}")
        return

    report_prompt = "请基于上述完整任务生成结项报告，要求：\n" \
                    "1. 列出所有参与组员及其贡献\n" \
                    "2. 总结整体工作成果\n" \
                    "3. 使用简洁的换行格式，不要使用句号\n" \
                    "4. 保持内容在200字以内"

    closing_report = chat(report_prompt)

    try:
        report_data = {
            "resultType": "closingReport",
            "closingReport": closing_report
        }
        socketserver.send(report_data)
    except Exception as e:
        print(f"发送结项报告错误: {e}")

    print("完整任务流程执行完毕")

if __name__ == "__main__":
    main()

