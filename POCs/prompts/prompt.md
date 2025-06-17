# 📝 SQL Query Breakdown & Explanation

This guide explains a multi-step SQL query designed to process a user’s search query, remove stopwords, and rank prompt suggestions using PostgreSQL full-text search. Each section uses an emoji icon for clarity and includes both the SQL and a plain-English explanation.

---

## 📋 Overview

The query follows these main steps:

1. **Clean and vectorize the user query**
2. **Split the query into words**
3. **Remove stopwords**
4. **Aggregate the remaining words**
5. **Rank prompt suggestions by similarity**
6. **Select and return the top results**

---

```sql
-- Step 1: Clean and vectorize the user's search query
WITH strip_query_cte AS (
    SELECT strip(to_tsvector('english', '{cleaned_query}'))::text AS query_vector_text
),

-- Step 2: Split the vectorized query into individual words
unnest_query_cte AS (
    SELECT unnest(string_to_array(query_vector_text, ' ')) AS word
    FROM strip_query_cte
),

-- Step 3: Remove stopwords specific to the application
stopword_removal_cte AS (
    SELECT word
    FROM unnest_query_cte
    WHERE word NOT IN (
        SELECT concat('''' ,stopword, '''')
        FROM {self.stopwords_table}
        WHERE app_id = {self.app_id}
    )
),

-- Step 4: Aggregate the remaining words into a processed query string
tv_cte AS (
    SELECT string_agg(word, ' ') AS processed_query
    FROM stopword_removal_cte
),

-- Step 5: Rank prompts based on similarity to the processed query
ranked_prompts AS (
    SELECT serial_id, article_id, keywords, prompt_suggestion,
        ts_rank(
            to_tsvector('english', prompt_suggestion || ' ' || keywords),
            to_tsquery('english', (
                SELECT replace(processed_query, ' ', ':* &') || ':*'
                FROM tv_cte
            ))
        ) AS rank
    FROM {self.heading_table}
)

-- Step 6: Select and order the top-ranked prompts
SELECT serial_id, article_id, keywords, prompt_suggestion, rank
FROM ranked_prompts
WHERE rank > 1.0e-20
ORDER BY rank DESC
LIMIT {top_k};
```
## 🗂️ Placeholders to Replace

1. **{cleaned_query}**: The user’s search string, cleaned for processing.
1. **{self.stopwords_table}**: The table containing your stopwords.
1. **{self.app_id}**: The application ID for filtering stopwords.
1. **{self.heading_table}**: The table containing prompts and keywords.
1. **{top_k}**: The number of top results to return.


## 💡 Notes

**This query uses PostgreSQL full-text search features.
Make sure your stopwords and heading tables are indexed for performance.
Adjust the rank > 1.0e-20 threshold as needed for your dataset.**