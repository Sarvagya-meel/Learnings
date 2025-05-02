# Learnings

### 📦 Activate Poetry Environment (Windows CMD)

To activate the Poetry-managed virtual environment manually from Command Prompt:

```
venv\Scripts\activate
```

Install Depency using poetry:
```
Poetry add <-packageName->
```

Install all dependecy from poetry lock:
```
poetry install --no-root 
```

You can also create a `activate_env.bat` file in your project directory with the same content to quickly activate it.
