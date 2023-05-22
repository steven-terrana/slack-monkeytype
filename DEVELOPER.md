# Developer Docs

## Tables

``` mermaid
erDiagram
leaderboards {
  string view "the view id of the leaderboard"
  string channel "the channel where the leaderboard modal was opened"
  object fragment "the current query fragment of the leaderboard"
}
```

``` mermaid
erDiagram
users {
  string username "a monkeytype username"
  string[] channels "the channels where this user is registered"
}
```

``` mermaid
erDiagram
settings {
  string view_id "the view of the leaderboard view"
  string duration "the slack block of the selected duration option"
  string difficulty "the slack block of the selected difficulty option"
  string punctuation "the slack block of the selected punctuation"
}
```

``` mermaid
erDiagram
bests {
  string user "the monkeytype user"
  string category "the unit of length of the test. either 'time' or 'words'"
  string duration "the length of the test"
  float wpm "calculated words per minute score"
  float raw "the actual wpm score"
  float acc "accuracy percent"
  float consistency "variance of raw wpm"
  string difficulty "the difficulty of the test"
  bool lazyMode "whether lazy mode was enabled or not"
  string language "the language of the test"
  bool punctuation "whether punctuation was enabled or not"
  integer timestamp "the epoch time of the test"
}
```
