from snowflake import SnowflakeGenerator


gen = SnowflakeGenerator(1)



def generate_id() -> str:
    return next(gen)