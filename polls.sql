BEGIN TRANSACTION;
CREATE TABLE polls
                 (poll_id SERIAL PRIMARY KEY, question TEXT);
CREATE TABLE options
                 (option_id SERIAL PRIMARY KEY, poll_id INTEGER, option TEXT, votes INTEGER);
CREATE TABLE votes
                 (vote_id SERIAL PRIMARY KEY, poll_id INTEGER, user_id BIGINT, option_id INTEGER);
CREATE TABLE poll_servers
                 (poll_id SERIAL PRIMARY KEY, server_id BIGINT);
COMMIT;
