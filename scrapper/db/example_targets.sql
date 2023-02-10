--scrapper_data_target
------ YOUTUBE

-- CHANNELS
INSERT INTO scrapper_data_target
(provider_id, target_type_id, video_type_id, enabled, data_url, description, channel_id, channel_name, target_rating, additional_data) VALUES

	 -- FULL
	(1,2,1,false,'https://www.youtube.com/@BilliSpeaks/videos','cat speaking keyboard','@BilliSpeaks','BilliSpeaks',0,NULL),

	 -- SHORTS
	 (1,2,2,false,'https://www.youtube.com/@BilliSpeaks/shorts','cat speaking keyboard','@BilliSpeaks','BilliSpeaks',0,NULL);

-- GLOBAL SEARCH QUERIES
INSERT INTO scrapper_data_target
(provider_id, target_type_id, video_type_id, enabled, data_url, description, channel_id, channel_name, target_rating, additional_data) VALUES
	 (1,3,2,false,'https://www.youtube.com/results?search_query=cat+%23shorts&sp=CAASAhAB','global search for shorts: "cat"',NULL,NULL,0,NULL),
	 (1,3,2,false,'https://www.youtube.com/results?search_query=neko+%23shorts&sp=CAASAhAB','global search for shorts: "neko"',NULL,NULL,0,NULL);


------ TIKTOK

-- CHANNELS
INSERT INTO scrapper_data_target
(provider_id, target_type_id, video_type_id, enabled, data_url, description, channel_id, channel_name, target_rating, additional_data) VALUES
	 (2,2,2,false,'https://www.tiktok.com/@meowisthebest1','couple of cats','@meowisthebest1','Meowisthebest',0,NULL);

-- GLOBAL SEARCH QUERIES
--TODO