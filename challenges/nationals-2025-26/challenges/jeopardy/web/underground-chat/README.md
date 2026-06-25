# underground-bank

**Author:** larry

**Category:** Web

## Description

We think we found an underground secret society that's up to no good. They seem to have setup some kind of "zero trust" chat system. Help infiltrate their ranks and figure out what they're up to...

### Files

[](./release_files/underground-chat.zip)

## Part 1

**CTFd name:** underground-chat

### CTFd Description

> We think we found an underground secret society that's up to no good. They seem to have setup some kind of "zero trust" chat system. Help infiltrate their ranks and figure out what they're up to...
> 
> File: [underground-chat.zip](attachment)
> Server: [http://{ip}:8080](http://{ip}:8080)

### Depends on

None

### Flag

<details>
<summary>(expand to read)</summary><br>

`FLAG=CyberSci{zero_trust_means_zer0_trust}`

</details>

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

There is a cookie parser differential between the chat server and the Envoy reverse proxy server. Envoy takes only the first cookie named `token`, but the chat server takes the last cookie named `token`.

The chat server does not verify the token, only decode it, thus we are looking for some kind of parser differential between the reverse proxy and the chat server.

Both the Envoy reverse proxy and the chat server only accept the first cookie with a given name, so there isn't an easy `token=x; token=y` trick.

```cpp
// https://github.com/envoyproxy/envoy/blob/main/source/common/http/utility.cc#L377C1-L393C2
absl::flat_hash_map<std::string, std::string>
Utility::parseCookies(const RequestHeaderMap& headers,
                      const std::function<bool(absl::string_view)>& key_filter) {
  absl::flat_hash_map<std::string, std::string> cookies;

  forEachCookie(headers, Http::Headers::get().Cookie,
                [&cookies, &key_filter](absl::string_view k, absl::string_view v) -> bool {
                  if (key_filter(k)) {
                    cookies.emplace(k, v);
                  }

                  // continue iterating until all cookies are processed.
                  return true;
                });

  return cookies;
}
```

We note that `.emplace()` in C++ will not overwrite an existing key, so if a cookie with the same name is already present, it will not be replaced.

```js
// https://github.com/jshttp/cookie/blob/master/src/index.ts#L133
export function parseCookie(str: string, options?: ParseOptions): Cookies {
  const obj: Cookies = new NullObject();
  const len = str.length;
  // RFC 6265 sec 4.1.1, RFC 2616 2.2 defines a cookie name consists of one char minimum, plus '='.
  if (len < 2) return obj;

  const dec = options?.decode || decode;
  let index = 0;

  do {
    const eqIdx = eqIndex(str, index, len);
    if (eqIdx === -1) break; // No more cookie pairs.

    const endIdx = endIndex(str, index, len);

    if (eqIdx > endIdx) {
      // backtrack on prior semicolon
      index = str.lastIndexOf(";", eqIdx - 1) + 1;
      continue;
    }

    const key = valueSlice(str, index, eqIdx);

    // only assign once
    if (obj[key] === undefined) {
      obj[key] = dec(valueSlice(str, eqIdx + 1, endIdx));
    }

    index = endIdx + 1;
  } while (index < len);

  return obj;
}
```

However, while the JavaScript cookie parsing logic ignores whitespace at the end of the cookie name, the Envoy implementation does not.

```js
// https://github.com/jshttp/cookie/blob/master/src/index.ts#L507
function valueSlice(str: string, min: number, max: number) {
  if (min === max) return "";
  let start = min;
  let end = max;

  do {
    const code = str.charCodeAt(start);
    if (code !== 32 /*   */ && code !== 9 /* \t */) break;
  } while (++start < end);

  while (end > start) {
    const code = str.charCodeAt(end - 1);
    if (code !== 32 /*   */ && code !== 9 /* \t */) break;
    end--;
  }

  return str.slice(start, end);
}
```

```cpp
// https://github.com/envoyproxy/envoy/blob/main/source/common/http/utility.cc#L338
void forEachCookie(
    const HeaderMap& headers, const LowerCaseString& cookie_header,
    const std::function<bool(absl::string_view, absl::string_view)>& cookie_consumer) {
  const Http::HeaderMap::GetResult cookie_headers = headers.get(cookie_header);

  for (size_t index = 0; index < cookie_headers.size(); index++) {
    auto cookie_header_value = cookie_headers[index]->value().getStringView();

    // Split the cookie header into individual cookies.
    for (const auto& s : StringUtil::splitToken(cookie_header_value, ";")) {
      // Find the key part of the cookie (i.e. the name of the cookie).
      size_t first_non_space = s.find_first_not_of(' ');
      size_t equals_index = s.find('=');
      if (equals_index == absl::string_view::npos) {
        // The cookie is malformed if it does not have an `=`. Continue
        // checking other cookies in this header.
        continue;
      }
      absl::string_view k = s.substr(first_non_space, equals_index - first_non_space);
      absl::string_view v = s.substr(equals_index + 1, s.size() - 1);

      // Cookie values may be wrapped in double quotes.
      // https://tools.ietf.org/html/rfc6265#section-4.1.1
      if (v.size() >= 2 && v.back() == '"' && v[0] == '"') {
        v = v.substr(1, v.size() - 2);
      }

      if (!cookie_consumer(k, v)) {
        return;
      }
    }
  }
}
```

Thus, you can send a request with a cookie like `Cookie: token ={spoof_token}; token={token}'` to pass the reverse proxy auth check and also pass the admin check on the chat server.
</details>

## Setup instructions

1. Run `docker compose up` to start the service.
2. Verify: Run `exploit.py` in the solve_files to ensure that the service is working
3. Upload `underground-chat.zip` as a CTFd attachment. Make sure port 8080 is open on the server.