from sqlalchemy import create_engine, or_, Column, Integer, String, Boolean, JSON, Float, Text, event
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from datetime import datetime, timedelta
import threading

DATABASE_URI = 'sqlite:///file-manager.db'
Base = declarative_base()

engine = create_engine(DATABASE_URI, connect_args={"check_same_thread": False})
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

lock = threading.Lock()

class FileShare(Base):
    __tablename__ = 'file_share'
    id = Column(Integer, primary_key=True)
    path = Column(String)
    file_name = Column(String)
    shared_url = Column(String)
    is_dir = Column(Boolean)
    description = Column(String)
    created_at = Column(String)
    request_list = Column(JSON, default=[])
    total_allowed_requests_per_ip = Column(Integer)
    total_allowed_requests = Column(Integer)
    total_requests_made = Column(Integer, default=0)
    download_and_view_list = Column(JSON, default=[])
    total_allowed_download_and_view_per_ip = Column(Integer)
    total_allowed_download_and_view = Column(Integer)
    total_download_and_view = Column(Integer, default=0)
    name = Column(String)
    random_id = Column(String, unique=True)
    password = Column(String)
    auto_download = Column(Boolean)

Base.metadata.create_all(engine)

def get_current_time_millis(days=0, hours=0, minutes=0):
    now = datetime.now()
    future_time = now + timedelta(days=days, hours=hours, minutes=minutes)
    future_time_millis = int(future_time.timestamp() * 1000)
    return future_time_millis

def add_file_share(path, file_name, shared_url, is_dir, description, total_allowed_requests_per_ip, total_allowed_requests, total_allowed_download_and_view_per_ip, total_allowed_download_and_view, name, random_id, password, auto_download):
    with lock:
        with Session() as session:
            created_at = get_current_time_millis()

            new_file_share = FileShare(
                path=path, file_name=file_name, shared_url=shared_url, is_dir=is_dir,
                description=description, created_at=created_at,
                total_allowed_requests_per_ip=total_allowed_requests_per_ip,
                total_allowed_requests=total_allowed_requests,
                total_allowed_download_and_view_per_ip=total_allowed_download_and_view_per_ip,
                total_allowed_download_and_view=total_allowed_download_and_view,
                name=name, random_id=random_id, password=password,
                auto_download=auto_download
            )
            session.add(new_file_share)
            session.commit()
            session.close()

def get_files_share():
    with lock:
        with Session() as session:
            files_share = session.query(FileShare).all()
            session.close()
            return files_share

def update_request_list_to_file_share(random_id, data):
    with lock:
        with Session() as session:
            file_share = session.query(FileShare).filter_by(random_id=random_id).first()
            if file_share:
                if file_share.request_list is None:
                    file_share.request_list = []

                file_share.total_requests_made += 1

                updated_list = file_share.request_list + [data]
                file_share.request_list = updated_list

                session.commit()

def update_download_list_to_file_share(random_id, data):
    with lock:
        with Session() as session:
            file_share = session.query(FileShare).filter_by(random_id=random_id).first()
            if file_share:
                if file_share.download_and_view_list is None:
                    file_share.download_and_view_list = []

                file_share.total_download_and_view += 1

                updated_list = file_share.download_and_view_list + [data]
                file_share.download_and_view_list = updated_list

                session.commit()

def get_file_share(random_id=None, shared_url=None):
    with lock:
        with Session() as session:
            filters = []
            if random_id is not None:
                filters.append(FileShare.random_id == random_id)
            if shared_url is not None:
                filters.append(FileShare.shared_url == shared_url)
            
            if filters:
                file_share = session.query(FileShare).filter(or_(*filters)).first()
                session.close()
                return file_share
