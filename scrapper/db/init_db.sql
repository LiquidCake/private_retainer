CREATE TABLE provider (
	provider_id SERIAL PRIMARY KEY,
	short_name TEXT NOT NULL,
	base_url TEXT NOT NULL,
	additional_data_json TEXT NOT NULL DEFAULT '{}',
	channel_url_template TEXT NOT NULL DEFAULT '{}',
	preview_img_extension TEXT NOT NULL DEFAULT '.jpg',
	embed_type TEXT NOT NULL DEFAULT 'iframe',
	video_aspect TEXT NOT NULL DEFAULT 'horizontal',
	preview_aspect TEXT NOT NULL DEFAULT 'horizontal'
);

CREATE TABLE video_status (
	video_status_id SERIAL PRIMARY KEY,
	short_name TEXT NOT NULL
);

CREATE TABLE video_type (
	video_type_id SERIAL PRIMARY KEY,
	short_name TEXT NOT NULL
);

CREATE TABLE video_category (
	category_id SERIAL PRIMARY KEY,
	category_name TEXT NOT NULL
);

CREATE TABLE scrapper_data_target_type (
	target_type_id SERIAL PRIMARY KEY,
	short_name TEXT NOT NULL
);

CREATE TABLE found_video (
	video_id SERIAL PRIMARY KEY,
	provider_video_id TEXT NOT NULL,
	url TEXT NOT NULL,
	embed_url TEXT NOT NULL,
	title TEXT NOT NULL,
	orig_title TEXT NOT NULL,
	video_type_id INTEGER NOT NULL,
	target_type_id INTEGER NOT NULL,
	provider_id INTEGER NOT NULL,
	channel_name TEXT NOT NULL,
	channel_id TEXT NOT NULL,
	category_ids INTEGER[] NOT NULL,
	video_status_id INTEGER NOT NULL,
	editors_pick BOOLEAN NOT NULL DEFAULT FALSE,
	available BOOLEAN NOT NULL DEFAULT TRUE,
	created_at TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
	uploaded_at TIMESTAMP NULL,
	
	FOREIGN KEY (provider_id) REFERENCES provider (provider_id),
	FOREIGN KEY (video_type_id) REFERENCES video_type (video_type_id),
	FOREIGN KEY (video_status_id) REFERENCES video_status (video_status_id),
	FOREIGN KEY (target_type_id) REFERENCES scrapper_data_target_type (target_type_id)
);

CREATE INDEX found_video_video_status_id_idx ON found_video (video_status_id);
CREATE INDEX found_video_created_at_idx ON found_video (created_at);

CREATE UNIQUE INDEX found_video_url_idx ON found_video (url);
CREATE UNIQUE INDEX found_video_provider_id_provider_video_id_idx ON found_video (provider_id, provider_video_id);


-- init data

-- provider
INSERT INTO provider (provider_id, short_name, base_url, additional_data_json, channel_url_template, preview_img_extension, embed_type, video_aspect, preview_aspect) VALUES
(1, 'youtube', 'https://www.youtube.com/', '{"data_url_tpl_by_video_type_id": {"1": "https://www.youtube.com/{}/videos", "2": "https://www.youtube.com/{}/shorts"}}', 'https://www.youtube.com/{}', '.jpg', 'iframe', 'horizontal', 'horizontal'),
(2, 'tiktok', 'https://www.tiktok.com/', '{"data_url_tpl_by_video_type_id": {"1": null, "2": "https://www.tiktok.com/{}"}}', 'https://www.tiktok.com/{}', '.png', 'html_insert', 'vertical', 'vertical');

SELECT setval('provider_provider_id_seq', (SELECT MAX(provider_id) FROM provider), true);

-- video_status
INSERT INTO video_status (video_status_id, short_name) VALUES (1, 'unapproved');
INSERT INTO video_status (video_status_id, short_name) VALUES (2, 'approved');
INSERT INTO video_status (video_status_id, short_name) VALUES (3, 'ignored');
INSERT INTO video_status (video_status_id, short_name) VALUES (4, 'uploaded');
INSERT INTO video_status (video_status_id, short_name) VALUES (5, 'suppressed');

SELECT setval('video_status_video_status_id_seq', (SELECT MAX(video_status_id) FROM video_status), true);

-- video_type
INSERT INTO video_type (video_type_id, short_name) VALUES (1, 'Full video');
INSERT INTO video_type (video_type_id, short_name) VALUES (2, 'Short');

SELECT setval('video_type_video_type_id_seq', (SELECT MAX(video_type_id) FROM video_type), true);

-- video_category
INSERT INTO video_category (category_id, category_name) VALUES (1, 'Chubby');
INSERT INTO video_category (category_id, category_name) VALUES (2, 'Red');

SELECT setval('video_category_category_id_seq', (SELECT MAX(category_id) FROM video_category), true);

-- scrapper_data_target_type
INSERT INTO scrapper_data_target_type (target_type_id, short_name) VALUES (1, 'other');
INSERT INTO scrapper_data_target_type (target_type_id, short_name) VALUES (2, 'channel');
INSERT INTO scrapper_data_target_type (target_type_id, short_name) VALUES (3, 'global_search');

SELECT setval('scrapper_data_target_type_target_type_id_seq', (SELECT MAX(target_type_id) FROM scrapper_data_target_type), true);


---
--- configuration
---

CREATE TABLE configuration (
	config_name TEXT NOT NULL,
	config_value TEXT NOT NULL,
	provider_id INTEGER NOT NULL,   --actual provider id or '-1'
	
	PRIMARY KEY(config_name, provider_id)
);

INSERT INTO configuration (config_name, config_value, provider_id) VALUES ('scrapper_job_enabled-scrapper_root', 'true', -1);
INSERT INTO configuration (config_name, config_value, provider_id) VALUES ('scrapper_job_enabled-scrapper_targets_list', 'true', -1);
INSERT INTO configuration (config_name, config_value, provider_id) VALUES ('scrapper_job_enabled-publish_videos', 'true', -1);
INSERT INTO configuration (config_name, config_value, provider_id) VALUES ('scrapper_job_provider_enabled', 'true', -1);
INSERT INTO configuration (config_name, config_value, provider_id) VALUES ('scrapper_job_data_target_parallelism', '10', -1);

INSERT INTO configuration (config_name, config_value, provider_id) VALUES ('scrapper_ignored_channels', '', -1);
INSERT INTO configuration (config_name, config_value, provider_id) VALUES ('scrapper_suppressed_title_words', 'compilation, dog, animal, homeless, shelter, rescue, ill, cripple, прикол, funny', -1);


---
--- scrapper job
---

CREATE TABLE scrapper_job_status (
	job_type TEXT PRIMARY KEY,      -- type:   ['scrapper_root', 'publish_videos']
	status TEXT NOT NULL,           -- status: ['started', 'finished']
	run_num INTEGER NOT NULL,
	started_at TIMESTAMP NOT NULL,
	finished_at TIMESTAMP NULL,
	finish_code TEXT NULL
);

INSERT INTO scrapper_job_status (job_type, status, run_num, started_at, finished_at) VALUES ('scrapper_root', 'finished', 0, NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC');
INSERT INTO scrapper_job_status (job_type, status, run_num, started_at, finished_at) VALUES ('scrapper_targets_list', 'finished', 0, NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC');
INSERT INTO scrapper_job_status (job_type, status, run_num, started_at, finished_at) VALUES ('publish_videos', 'finished', 0, NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC');


CREATE TABLE scrapper_job_log (
	log_id SERIAL PRIMARY KEY,
	job_type TEXT NOT NULL,
	run_num INTEGER NOT NULL,
	log_line TEXT NOT NULL,
	created_at TIMESTAMP NOT NULL,
	
	FOREIGN KEY (job_type) REFERENCES scrapper_job_status (job_type)
);


CREATE TABLE scrapper_data_target (
	target_id SERIAL PRIMARY KEY,
	provider_id INTEGER NOT NULL,
	target_type_id INTEGER NOT NULL,
	video_type_id INTEGER NOT NULL,
	enabled BOOLEAN NOT NULL DEFAULT TRUE,
	data_url TEXT NOT NULL,
	description TEXT NULL,
	channel_id TEXT NULL,
	channel_name TEXT NULL,
	target_rating INTEGER NOT NULL DEFAULT 0,
	additional_data TEXT NULL,
	last_scrapped_at TIMESTAMP NULL,
	last_fully_scrapped_at TIMESTAMP NULL,
	last_scrapped_provider_video_id TEXT NULL,
	
	FOREIGN KEY (target_type_id) REFERENCES scrapper_data_target_type (target_type_id),
	FOREIGN KEY (video_type_id) REFERENCES video_type (video_type_id),
	FOREIGN KEY (provider_id) REFERENCES provider (provider_id)
);

CREATE INDEX scrapper_data_target_provider_id_enabled_idx ON scrapper_data_target (provider_id, enabled);

CREATE UNIQUE INDEX scrapper_data_target_data_url_idx ON scrapper_data_target (data_url);


CREATE TABLE scrapper_data_target_parsing_code (
	provider_id INTEGER NOT NULL,
	target_type_id INTEGER NOT NULL,
	video_type_id INTEGER NOT NULL,
	parsing_code TEXT NOT NULL,
	vars TEXT NOT NULL DEFAULT '{}',
	script_name TEXT NOT NULL,
	
	PRIMARY KEY(provider_id, target_type_id, video_type_id),
	FOREIGN KEY (target_type_id) REFERENCES scrapper_data_target_type (target_type_id),
	FOREIGN KEY (provider_id) REFERENCES provider (provider_id)
);

-- insert data from commited script files
INSERT INTO scrapper_data_target_parsing_code
(provider_id, target_type_id, video_type_id, parsing_code, vars, script_name) VALUES
	(1, 2, 1, '!!! insert contents of parser_youtube_channel.py', '{}'::text, 'parser_youtube_channel.py'),
	(1, 2, 2, '!!! insert contents of parser_youtube_channel_shorts.py', '{}'::text, 'parser_youtube_channel_shorts.py'),
	(1, 3, 2, '!!! insert contents of parser_youtube_global_search_shorts.py', '{}'::text, 'parser_youtube_global_search_shorts.py'),
	(2, 2, 2, '!!! insert contents of parser_tiktok_channel_shorts.py', '{}'::text, 'parser_tiktok_channel_shorts.py');