---
--- these table's are used by the SqliteDB interface.
--- note: this db is usualy created and maintained by the doorlock-web package.
---


CREATE TABLE IF NOT EXISTS "doorlock_tag" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "hwid" varchar(24) NOT NULL UNIQUE, "name" varchar(64) NOT NULL, "access" bool NOT NULL, "create_date" datetime NOT NULL, "update_date" datetime NOT NULL);
CREATE TABLE IF NOT EXISTS "doorlock_unkowntag" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "create_date" datetime NOT NULL, "hwid" varchar(24) NOT NULL);

