from sqlalchemy import Column, Integer, String, Boolean, DateTime, ARRAY
from sqlalchemy.ext.declarative import declarative_base

base = declarative_base()

class FoundVideo(base):
    __tablename__ = 'found_video'

    video_id = Column(Integer, primary_key=True)
    provider_video_id = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    embed_url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    orig_title = Column(String, nullable=False)
    video_type_id = Column(Integer, nullable=False)
    target_type_id = Column(Integer, nullable=False)
    provider_id = Column(Integer, nullable=False)
    channel_name = Column(String, nullable=False)
    channel_id = Column(String, nullable=False)
    category_ids = Column(ARRAY(Integer, zero_indexes=True), nullable=False)
    video_status_id = Column(Integer, nullable=False)
    editors_pick = Column(Boolean, nullable=False)
    available  = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=False), nullable=False)
    uploaded_at = Column(DateTime(timezone=False), nullable=False)

    def __repr__(self):
        return '(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' % \
            (self.video_id, self.provider_video_id, self.url, self.embed_url, self.title, \
                self.orig_title, self.video_type_id, self.target_type_id, self.provider_id, self.channel_name, \
                    self.channel_id, self.category_ids, self.video_status_id, self.editors_pick, \
                        self.available, self.created_at, self.uploaded_at)
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class VideoProvider(base):
    __tablename__ = 'provider'

    provider_id = Column(Integer, primary_key=True)
    short_name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    channel_url_template = Column(String, nullable=False)
    preview_img_extension = Column(String, nullable=False)
    embed_type = Column(String, nullable=False)
    video_aspect = Column(String, nullable=False)
    preview_aspect = Column(String, nullable=False)
    additional_data_json = Column(String, nullable=False)

    def __repr__(self):
        return '(%s, %s, %s, %s, %s, %s, %s)' % \
            (self.provider_id, self.short_name, self.base_url, self.channel_url_template, self.preview_img_extension, self.embed_type, self.video_aspect,  self.preview_aspect)

class VideoStatus(base):
    __tablename__ = 'video_status'

    video_status_id = Column(Integer, primary_key=True)
    short_name = Column(String, nullable=False)

    def __repr__(self):
        return '(%s, %s)' % \
            (self.video_status_id, self.short_name)

class VideoType(base):
    __tablename__ = 'video_type'

    video_type_id = Column(Integer, primary_key=True)
    short_name = Column(String, nullable=False)

    def __repr__(self):
        return '(%s, %s)' % \
            (self.video_type_id, self.short_name)

class VideoCategory(base):
    __tablename__ = 'video_category'

    category_id = Column(Integer, primary_key=True)
    category_name = Column(String, nullable=False)

    def __repr__(self):
        return '(%s, %s)' % \
            (self.category_id, self.category_name)

class Configuration(base):
    __tablename__ = 'configuration'

    config_name = Column(String, primary_key=True)
    config_value = Column(String, nullable=False)
    provider_id = Column(Integer, primary_key=True)

#
# scrapper job
#

class ScrapperJobLog(base):
    __tablename__ = 'scrapper_job_log'

    log_id = Column(Integer, primary_key=True)
    job_type = Column(String, nullable=False) 
    run_num = Column(Integer, nullable=False)
    log_line = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=False), nullable=False)

class ScrapperJobStatus(base):
    __tablename__ = 'scrapper_job_status'

    job_type = Column(String, primary_key=True)
    status = Column(String, nullable=False)
    run_num = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=False), nullable=False)
    finished_at = Column(DateTime(timezone=False))
    finish_code = Column(String)

class ScrapperDataTargetType(base):
    __tablename__ = 'scrapper_data_target_type'

    target_type_id = Column(Integer, primary_key=True)
    short_name = Column(String, nullable=False)

class ScrapperDataTarget(base):
    __tablename__ = 'scrapper_data_target'

    target_id = Column(Integer, primary_key=True)
    target_type_id = Column(Integer, nullable=False)
    video_type_id = Column(Integer, nullable=False)
    provider_id = Column(Integer, nullable=False)
    enabled = Column(Boolean, nullable=False)
    data_url = Column(String, nullable=False)
    description = Column(String)
    channel_id = Column(String)
    channel_name = Column(String)
    target_rating = Column(Integer, nullable=False)
    additional_data = Column(String)
    last_scrapped_at = Column(DateTime(timezone=False))
    last_fully_scrapped_at = Column(DateTime(timezone=False))
    last_scrapped_provider_video_id = Column(String)

    def __repr__(self):
        return '(%s, %s, %s, %s, %s)' % \
            (self.target_id, self.target_type_id, self.video_type_id, self.data_url, self.channel_id)

class ScrapperDataTargetParsingCode(base):
    __tablename__ = 'scrapper_data_target_parsing_code'

    provider_id = Column(Integer, nullable=False, primary_key=True)
    target_type_id = Column(Integer, nullable=False, primary_key=True)
    video_type_id = Column(Integer, nullable=False, primary_key=True)
    parsing_code = Column(String, nullable=False)
    vars = Column(String, nullable=False)
    script_name = Column(String, nullable=False)
