from langchain_core.messages import AIMessageChunk

data = {
    "event": "on_chat_model_end", 
    "data": {
        "output": AIMessageChunk(
            content="八十一难中的第五难是“出城逢虎”，描述了唐僧师徒四人在出城时遇到老虎的困难和考验。", 
            additional_kwargs={}, 
            response_metadata={
                "model_provider": "openai", 
                "finish_reason": "stop", 
                "model_name": "gpt-4.1-mini-2025-04-14", 
                "system_fingerprint": "fp_a7294185dc", 
                "service_tier": "default"
            }, 
            id="lc_run--019ebaa1-ada1-7e00-b7e2-156cc60b8420", 
            tool_calls=[], 
            invalid_tool_calls=[], 
            usage_metadata={
                "input_tokens": 5508, 
                "output_tokens": 37, 
                "total_tokens": 5545, 
                "input_token_details": {"audio": 0, "cache_read": 0}, 
                "output_token_details": {"audio": 0, "reasoning": 0}
            }, 
            tool_call_chunks=[]
        )
    }, 
    "run_id": "019ebaa1-ada1-7e00-b7e2-156cc60b8420", 
    "name": "ChatOpenAI", 
    "tags": [], 
    'metadata': {
        'ls_provider': 'openai', 
        'ls_model_name': 'gpt-4.1-mini', 
        'ls_model_type': 'chat', 
        'ls_temperature': None, 
        'ls_integration': 'langchain_chat_model'
    }, 
    'parent_ids': []
}


content='True' 
additional_kwargs={'refusal': None} 
response_metadata={
    'token_usage': {
        'completion_tokens': 2, 
        'prompt_tokens': 159, 
        'total_tokens': 161, 
        'completion_tokens_details': {
            'accepted_prediction_tokens': 0, 
            'audio_tokens': 0, 
            'reasoning_tokens': 0, 
            'rejected_prediction_tokens': 0
        }, 
        'prompt_tokens_details': {
            'audio_tokens': 0, 
            'cached_tokens': 0
        }, 
        'latency_checkpoint': {
            'engine_tbt_ms': 4, 
            'engine_ttft_ms': 43, 
            'engine_ttlt_ms': 52, 
            'pre_inference_ms': 86, 
            'service_tbt_ms': 28, 
            'service_ttft_ms': 169, 
            'service_ttlt_ms': 192, 
            'total_duration_ms': 138, 
            'user_visible_ttft_ms': 82
        }
    }, 
    'model_provider': 'openai', 
    'model_name': 'gpt-4.1-mini-2025-04-14', 
    'system_fingerprint': 'fp_a7294185dc', 
    'id': 'chatcmpl-Dpq9wlEwAgf6MiAVM8LtZMqsYVfG1', 
    'service_tier': 'default', 'finish_reason': 'stop', 
    'logprobs': None} 
id='lc_run--019ebaa1-6251-7081-8b7b-c3e13e5104c6-0' 
tool_calls=[] 
invalid_tool_calls=[] 
usage_metadata={
    'input_tokens': 159, 
    'output_tokens': 2, 
    'total_tokens': 161, 
    'input_token_details': {'audio': 0, 'cache_read': 0}, 
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             'output_token_details': {'audio': 0, 'reasoning': 0}}