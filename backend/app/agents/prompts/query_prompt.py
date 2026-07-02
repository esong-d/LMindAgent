from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def build_chitchat_prompt() -> ChatPromptTemplate:
    """
    system:
        你是一名 AI 助手。
        当前用户的问题无需查询知识库，请直接根据你的已有知识回答。
        要求：
        1. 回答准确、自然、简洁。
        2. 请结合历史对话理解当前问题，保持上下文一致。
        3. 如果问题是上一轮的追问，请继续回答，不要重新开始新的话题。
        4. 如果不知道答案，请直接说明，不要编造事实。
        5. 根据问题复杂程度调整回答长度：
        - 简单问题简洁回答；
        - 复杂问题提供适当的解释。
        6. 如有必要，可使用 Markdown（标题、列表、代码块）提高可读性。
    
    human:
        用户问题：{query}
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                'system',
                """
                You are an AI assistant.
                The current user's question does not require consulting the knowledge base; please answer directly based on your existing knowledge.
                Requirements:
                1. Answer accurately, naturally, and concisely.
                2. Understand the current question by referring to past conversations and maintain contextual consistency.
                3. If the question is a follow-up question from a previous round, please continue answering; do not start a new topic.
                4. If you do not know the answer, please state it directly; do not fabricate facts.
                5. Adjust the length of your answer according to the complexity of the question:
                - Simple questions: Answer concisely;
                - Complex questions: Provide appropriate explanations.
                6. If necessary, use Markdown (headings, lists, code blocks) to improve readability.
                """
            ),
            MessagesPlaceholder("history"),
            (
                'human',
                """
                User question: {query}
                """
            ),
        ]
    )


def build_query_check_prompt() -> ChatPromptTemplate:
    """
    system:
        你是一个知识库查询校验器。
        任务：
        判断用户输入是否是“可用于知识库检索的有效查询”。

        判定标准：
        - 如果用户在明确询问一个事实、概念、方法、原因、步骤、定义、对错、比较等，并且可以转成检索问题，则返回 True。
        - 如果只是寒暄、碎片词、无意义文本、单纯陈述、表达不完整到无法检索，则返回 False。

        严格输出要求：
        - 只能输出 True 或 False
        - 不要输出解释、标点、空格、换行
    
    human:
        用户问题：{query}
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                'system',
                """
                You are a knowledge base query validator.
                Task:
                Determine if the user's input is a "valid query that can be used for knowledge base retrieval".
                Judgment Criteria:
                    - If the user is clearly asking about a fact, concept, method, reason, step, definition, right or wrong, comparison, etc., and can be converted into a retrieval question, return True.
                    - If it is just small talk, fragmented words, meaningless text, simple statements, or incomplete expression that cannot be retrieved, return False.
                Strict Output Requirements:
                    - Only output True or False.
                    - Do not output explanations, punctuation, spaces, or line breaks.
                """
            ),
            (
                'human',
                """
                User question: {query}
                """,
            ),
        ]
    )


def build_multi_query_prompt() -> ChatPromptTemplate:
    """
    system:
        你是一个问题拆分器。
        把用户问题拆成多个适合知识库检索的子问题。
        要求：
        1. 如果只有一个问题，只返回一个
        2. 每个子问题要独立、明确
        3. 只输出 list 数组问题， 严格执行输出要求，例如：
        ["问题1", "问题2"]
    human:
        用户问题：{query}
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                'system',
                """
                You are a question splitter.
                Break a user's question into multiple sub-questions suitable for knowledge base retrieval.
                Requirements:
                1. If there is only one question, return only one.
                2. Each sub-question must be independent and clearly defined.
                3. Only output a list of questions, strictly adhering to the output requirements, for example: ["Question 1", "Question 2"]
                """
            ),
            MessagesPlaceholder("history"),
            (
                'human',
                """
                User question: {query}
                """
            ),
        ]
    )

def build_route_prompt() -> ChatPromptTemplate:
    """
    system:
        你是一个RAG系统的路由器。
        你的任务是判断回答用户的问题是否需要检索企业知识库。
        请结合历史对话和用户问题，判断是否需要检索知识库。
        类别：
        - chitchat: 闲聊、问候、自我介绍等, 例如: "你好", "你是谁"等
        - rag: 需要查询知识库的问题, 例如: "文档中提到过哪些方法"

        只返回: rag或chitchat
        请严格执行返回格式输出，不要输出任何解释。
    human:
        用户问题：{query}
    """
    return ChatPromptTemplate.from_messages(
        [
            (
            'system',
            """
            You are a router in a RAG system.
            Your task is to determine whether answering a user's question requires searching the enterprise knowledge base.
            Please combine historical conversations and user questions to determine whether a knowledge base search is necessary.
            Categories:
            - chitchat: Small talk, greetings, self-introductions, etc., e.g., "Hello", "Who are you?"
            - rag: Questions requiring a knowledge base search, e.g., "What methods are mentioned in the documentation?"
            Return only: rag or chitchat
            Please strictly adhere to the return format and do not provide any explanation.
            """
            ),
            MessagesPlaceholder("history"),
            (
                'human',
                """
                User question: {query}
                """
            ),
        ]
    )


def build_rewrite_query_prompt() -> ChatPromptTemplate:
    """
    system:
        你是一个检索查询改写器。
        请把用户问题改写成适合知识库检索的简洁 query。
        要求：
        1. 保留核心语义
        2. 去掉口语、废话
        3. 如果上下文有指代，补全指代
        4. 只输出改写后的 query, 不要解释
        5. 每个子问题要独立、明确
        6. 请严格返回JSON数组, 不做任何解释, 例如：["问题1", "问题2"]
    human:
        用户问题：{query}
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                'system',
                """
                You are a query rewriter.
                Please rewrite user questions into concise queries suitable for knowledge base retrieval.
                Requirements:
                1. Preserve the core semantics.
                2. Remove colloquialisms and unnecessary words.
                3. Complete the pronouns if the context provides them.
                4. Output only the rewritten query; do not provide explanations.
                5. Each subquestion should be independent and explicit.
                6. Please strictly return a JSON array without any explanation, e.g., ["Question 1", "Question 2"].
                """
            ),
            MessagesPlaceholder("history"),
            (
                'human',
                """
                User question: {query}
                """,
            ),
        ]
    )



def build_keywords_prompt() -> ChatPromptTemplate:
    """
    system:
        你是一个专业的关键词提取助手。
        任务：从用户问题中提取最重要的检索关键词。

        要求：
        1. 保留技术术语、产品名、框架名等。
        2. 去除停用词和无意义词。
        3. 输出3~8个关键词。
        4. 请严格返回JSON数组, 不做任何解释, 例如: ["大模型", "LLM", "ChatGPT"]。
    human:
        用户问题：{query}
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                'system',
                """
                You are a professional keyword extraction assistant.
                Task: Extract the most important search keywords from user questions.
                Requirements:
                1. Retain technical terms, product names, framework names, etc.
                2. Remove stop words and meaningless words.
                3. Output 3-8 keywords.
                4. Please strictly return a JSON array without any interpretation, for example: ["Large Model", "LLM", "ChatGPT"].
                """
            ),
            (
                'human',
                """
                User question: {query}
                """
            ),
        ]
    )