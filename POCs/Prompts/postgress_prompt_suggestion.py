"""
Author: Sarvagya Meel
Email: sarvagyameel2@gmail.com
Date: 05/02/25
"""
import os
from abc import ABC
from functools import reduce
from typing import Any

from pydantic import BaseModel
from base_prompt_suggestion import BasePromptSuggestion
from POCs.DBs.Pg_Vector.db_ops import get_connection
class PromptSuggestion(BaseModel):
    suggestion: str = None
    source: str= None


class PostGressPromptSuggestion(BasePromptSuggestion, ABC):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.connection = get_connection()
        self.heading_table = os.getenv('DB_HEADING_TABLE')
        self.stopwords_table = os.getenv('DB_STOPWORDS_TABLE')
        self.app_id = "test"

    def get_prompt_suggestions(self, query_text:str, top_k:int)-> [PromptSuggestion]:
        suggestions = []
        cursor = self.connection.cursor()

        # Preclean Up for removing unintended and affectioning words
        replacements = [
            ("#",""),("'",""),('"',""),
        ]

        cleaned_query = reduce(lambda text, rep:text.replace(*rep),replacements, query_text.lower())
        try:
            sql = f"""
            WITH strip query_cte AS (
                SELECT strip(to_tsvector('english', '{cleaned_query}'))::text AS query_vector_text
                ),
            unnest query-cte AS (
               SELECT unnest(string_to_array(query_vector_text, '')) AS word FROM strip_query_cte
               ),
            stopword_removal_cte AS (
                SELECT word FROM unnest-query_cte WHERE word NOT IN (
                SELECT concat('''' ,stopword, '''') FROM {self.stopwords_table} WHERE app_id = {self.app_id}
                    )
                )
            tv_cte AS ( SELECT string_agg(word, '') AS processed_query FROM stopword_removal_cte
            );
            ranked_prompts AS (
                SELECT serial_id, artcle_id, keywords, prompt_suggestion,
                ts_rank(
                    to_tsvector('english', prompt_suggestion || ' ' || keywords),
                    to_tsquery ('english', ( SELECT replace(processed_query,' ', ':* &') || ':*' AS user_query FROM tv_cte))
                    ) AS RANK
                FROM {self.heading_table}
            )
            SELECT serial_id, article_id, keywords, prompt_suggestion, rank
            FROM ranked_prompts
            WHERE rank > 1.0-20
            ORDER BY rank DESC
            LIMIT {top_k}
            """
            cursor.execute(sql)
            results = cursor.fetchall()

            if len(results) == 0:
                raise RuntimeWarning("No results found")
            for i, result in enumerate(results):
                suggestion = PromptSuggestion(suggestion=result[0], source=result[1])
                suggestions.append(suggestion)
        except Exception as e:
            print(e)
        except RuntimeWarning as e:
            print(e)
        return suggestions



if __name__ == '__main__':
    print('Python')
