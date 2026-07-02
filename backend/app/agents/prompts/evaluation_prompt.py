


from langchain_core.prompts import ChatPromptTemplate


def build_eval_generate_question_prompt() -> ChatPromptTemplate:
    """
    system:
    你是一个专业的提问专家, 擅长根据文档内容生成高质量检索问题和答案
    请根据用户输入的问题内容，生成指定数量的高质量检索问题。
    生成的问题应与原问题语义一致，覆盖不同表达方式，以提升知识检索的召回率。

    要求:
    1. 用户真实会问
    2. 不要直接照抄原文
    3.不要返回 markdown, 不要返回 ```json, 不要返回解释
    4.用于做rag测评使用的, 能有效帮助rag应用的测评
    5.返回json列表, 例如:json包含问题, 答案, chunk_id 列表(键对应只能是question, answer, chunk_id)

    human:
    高质量检索问题数量:{count} 个
    内容:{text}
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a professional question-asking expert, skilled at generating high-quality search questions and answers based on document content.
                Please generate a specified number of high-quality search questions based on user-inputted questions.
                The generated questions should be semantically consistent with the original questions and cover different expressions to improve the recall rate of knowledge retrieval.
                Requirements:
                1. Questions that users would actually ask.
                2. Do not directly copy the original text.
                3. Do not return Markdown, do not return JSON, and do not return explanations.
                4. For use in rag application evaluation; effectively aids in the evaluation of rag applications.
                5. Return a JSON list, for example: a JSON containing questions, answers, and a list of chunk_ids (keys can only correspond to question, answer, and chunk_id).
                """,
            ),
            (
                "human",
                """
                Number of high-quality search questions: {count}
                Content: {text}
                """
            )
        ]
    )


def build_check_eval_answer_correctness_prompt() -> ChatPromptTemplate:
    """
    system:
    你是一位严格的问答质量评估专家。
    请根据用户问题和标准答案，评估模型回答是否正确。
    评判标准：
    1. 模型回答与标准答案是否一致
    2. 模型回答是否准确
    3. 模型回答是否完整
    4. 模型回答是否流畅

    评估结果: 给模型回答评分, 0-1分, 0分表示完全错误, 1分表示完全正确
    最终返回json格式数据, 不要返回 markdown, 不要返回 ```json, 返回结果包含score, reason(做简洁解释)

    human:
    问题:{question}
    标准答案:{answer}
    模型回答:{model_answer}
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a rigorous question-and-answer quality assessment expert.
                Please evaluate the correctness of the model's answer based on the user's question and the standard answer.
                Evaluation Criteria:
                1. Does the model's answer match the standard answer?
                2. Is the model's answer accurate?
                3. Is the model's answer complete?
                4. Is the model's answer fluent?
                Evaluation Results: Rate the model's answer on a scale of 0-1, where 0 indicates complete error and 1 indicates complete correctness.
                The final result should be returned in JSON format. Do not return Markdown or `.json`. The returned result should include the score and a concise explanation of the reason.
                """
            ),
            (
                "human",
                """
                Question: {question}
                Standard Answer: {answer}
                Model Answer: {model_answer}
                """
            )
        ]
    )

def build_check_eval_answer_faithfulness_prompt() -> ChatPromptTemplate:
    """"
    system:
    你是一位严格的问答质量评估专家。
    请根据用户问题和标准答案，评估模型回答是否忠实于原文。
    请判断模型回答是否完全可以由检索上下文支持。
    注意：
    如果回答包含Context没有提到的信息,
    认为存在幻觉(Hallucination)。

    评判标准：
    1. 模型回答是否忠实于原文
    2. 模型回答是否准确
    3. 模型回答是否完整
    4. 模型回答是否流畅

    评估结果: 给模型回答评分, 0-1分, 0分表示完全不忠实, 1分表示完全忠实于原文
    最终返回json格式数据, 不要返回 markdown, 不要返回 ```json, 返回结果包含score, reason(做简洁解释)

    human:
    问题:{question}
    模型回答:{model_answer}
    检索上下文:{context}
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a rigorous question-and-answer quality assessment expert.
                Based on the user's question and the standard answer, evaluate whether the model's response is faithful to the original text.
                Please determine whether the model's response is fully supported by the retrieval context.
                Note:
                If the response contains information not mentioned in the context,
                hallucination is considered.
                Evaluation Criteria:
                1. Faithfulness of the model's response to the original text
                2. Accuracy of the model's response
                3. Completeness of the model's response
                4. Fluency of the model's response
                Evaluation Results: Rate the model's response from 0 to 1, where 0 indicates complete fidelity and 1 indicates complete fidelity.
                The final result should be returned in JSON format. Do not return Markdown or `.json`. The returned result should include a score and a concise explanation of the reason.
                """
            ), 
            (
                "human",
                """
                Question: {question}
                Model answer: {model_answer}
                Retrieval context: {context}
                """
            )
        ]
    )