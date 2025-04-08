from sqlalchemy.ext.declarative import declarative_base

# Base는 모든 모델 클래스의 부모 클래스로 사용돼.
# SQLAlchemy는 이 Base를 통해 모델 클래스와 실제 DB 테이블을 매핑함.
# 즉, Base를 상속받은 클래스만 실제 테이블로 인식됨.

Base = declarative_base()
