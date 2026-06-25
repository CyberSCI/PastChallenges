# Bot Random Actions Plan

## Goal
Add random API actions to `UserBot.run()` in `scripts/bot.py`.

## File to modify
`scripts/bot.py`

## New methods on `UserBot`

All methods: `async def action_name(self, client: AsyncClient)` — wrapped in try/except (catch `Exception`, print warning, continue).

### 1. `list_bulletins`
```python
await client.get("/api/bulletins/")
```

### 2. `view_random_bulletin`
```python
bulletin_id = random.randint(1, 4)
await client.get(f"/api/bulletins/{bulletin_id}/")
```

### 3. `list_posts`
```python
await client.get("/api/bulletins/posts/")
```

### 4. `view_random_post`
```python
response = await client.get("/api/bulletins/posts/")
posts = response.json()
if posts:
    post = random.choice(posts)
    await client.get(f"/api/bulletins/posts/{post['id']}/")
```

### 5. `create_post`
```python
TITLES = ["Status Update", "Quick Note", "Thoughts", "FYI", "Heads Up", "Report", "Reminder"]
BODIES = ["Nothing to report.", "All clear.", "Please review.", "See attached.", "Updated.", "Acknowledged.", "Will follow up."]
bulletin_id = random.randint(1, 4)
await client.post(f"/api/bulletins/{bulletin_id}/posts/", json={
    "title": random.choice(TITLES),
    "body": random.choice(BODIES),
})
```

### 6. `comment_on_post`
```python
COMMENTS = ["Noted.", "Thanks.", "Got it.", "Acknowledged.", "Will do.", "Roger.", "Copy that.", "Understood."]
response = await client.get("/api/bulletins/posts/")
posts = response.json()
if posts:
    post = random.choice(posts)
    await client.post(f"/api/bulletins/posts/{post['id']}/comments/", json={
        "body": random.choice(COMMENTS),
    })
```

### 7. `list_comments`
```python
await client.get("/api/bulletins/comments/")
```

### 8. `view_logs`
```python
levels = ["info", "warning", "error", "debug"]
await client.get("/api/system/logs/", params={"level": random.choice(levels), "size": 10})
```

## Changes to `run()`

```python
async def run(self):
    actions = [
        self.list_bulletins,
        self.view_random_bulletin,
        self.list_posts,
        self.view_random_post,
        self.create_post,
        self.comment_on_post,
        self.list_comments,
        self.view_logs,
    ]
    async with self.new_client() as client:
        await asyncio.sleep(random.randint(1, 4))
        await self.login(client)
        selected = random.sample(actions, k=random.randint(3, 6))
        for action in selected:
            await asyncio.sleep(random.uniform(0.5, 2.0))
            try:
                await action(client)
            except Exception as e:
                print(f"Bot {self.bot_id}: {action.__name__} failed: {e}")
```

## Constants
Move `TITLES`, `BODIES`, `COMMENTS` to module level to avoid recreation.
