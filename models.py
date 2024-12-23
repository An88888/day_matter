from datetime import datetime, timedelta
from celery import schedules
from extensions import db

class User(db.Model):
    __tablename__ = 'users'  # 表名

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, info={"description": "用户名"})
    password = db.Column(db.String(128), nullable=False, info={"description": "密码"})
    is_admin = db.Column(db.Boolean, default=False, info={"description": "是否管理员"})
    device_key = db.Column(db.String(80), unique=True, nullable=True, info={"description": "bark编码"})

    events = db.relationship('Event', backref='user', lazy=True)
    food = db.relationship('Food', back_populates='user', lazy=True)
    cate = db.relationship('Cate', back_populates='user', lazy=True)
    ingredient = db.relationship('Ingredient', back_populates='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}, Admin: {self.is_admin}>'


class Event(db.Model):
    __tablename__ = 'events'  # 表名

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(120), nullable=False, info={"description": "事件名称"})
    target_date = db.Column(db.Date, nullable=False, info={"description": "指定日期"})
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, info={"description": "用户ID"})
    status = db.Column(db.String(20), info={"description": "事件状态（1: 进行中, 2: 已结束）"})

    def __repr__(self):
        return f'<Event {self.name}, Target Date: {self.target_date}, User ID: {self.user_id}>'

class ScheduledTask(db.Model):
    __tablename__ = 'scheduled_tasks'  # 表名

    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(100), nullable=False, info={"description": "任务名称"})
    task_type = db.Column(db.String(100), nullable=False, info={"description": "任务函数名"})
    frequency = db.Column(db.String(50), nullable=True, info={"description": "调度频率"})
    last_run = db.Column(db.DateTime, default=datetime.utcnow, info={"description": "上次运行时间"})
    is_active = db.Column(db.Boolean, default=True, info={"description": "是否激活（False: 不激活, True: 激活）"})
    created_at = db.Column(db.DateTime, default=datetime.utcnow, info={"description": "任务创建时间"})
    is_periodic = db.Column(db.Boolean, default=False, info={"description": "是否为周期任务"})
    schedule_type= db.Column(db.String(20), info={"description": "调度方式（crontab, interval）"})

    crontab_id = db.Column(db.Integer, db.ForeignKey('crontab_schedules.id'), nullable=True)
    interval_id = db.Column(db.Integer, db.ForeignKey('interval_schedules.id'), nullable=True)

    def __repr__(self):
        return f"<ScheduledTask(name={self.name}, task_type={self.task_type}, frequency={self.frequency})>"

class CrontabSchedule(db.Model):
    __tablename__ = 'crontab_schedules'  # 表名

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)  # 主键
    minute = db.Column(db.String(64), default='*', info={"description": "分钟"})
    hour = db.Column(db.String(64), default='*', info={"description": "小时"})
    day_of_week = db.Column(db.String(64), default='*', info={"description": "星期"})
    day_of_month = db.Column(db.String(64), default='*', info={"description": "月份中的日期"})
    month_of_year = db.Column(db.String(64), default='*', info={"description": "年份中的月份"})

    def __repr__(self):
        return '{0} {1} {2} {3} {4} (m/h/d/dM/MY)'.format(
            self.minute, self.hour, self.day_of_week, self.day_of_month, self.month_of_year,
        )

    @property
    def schedule(self):
        # 返回调度对象，用于 Celery 任务调度
        return schedules.crontab(
            minute=self.minute,
            hour=self.hour,
            day_of_week=self.day_of_week,
            day_of_month=self.day_of_month,
            month_of_year=self.month_of_year
        )

class IntervalSchedule(db.Model):
    __tablename__ = 'interval_schedules'  # 表名

    PERIOD_CHOICES = [
        ('seconds', 'Seconds'),
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
    ]

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)  # 主键
    every = db.Column(db.Integer, nullable=False, info={"description": "间隔数量"})
    period = db.Column(db.String(24), nullable=False, info={"description": "时间单位", "choices": PERIOD_CHOICES})  # 例如：秒、分钟、小时等

    def __repr__(self):
        if self.every == 1:
            return f'every {self.period[:-1]}'  # 返回单数形式
        return f'every {self.every} {self.period}'  # 返回复数形式

    @property
    def schedule(self):
        # 返回调度对象，用于 Celery 任务调度
        return schedules.schedule(timedelta(**{self.period: self.every}))

from datetime import datetime
from extensions import db


class Food(db.Model):
    __tablename__ = 'food'  # 表名

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)  # 主键ID
    name = db.Column(db.String(100), nullable=False, info={"description": "菜名"})  # 菜名
    procedure = db.Column(db.Text, nullable=False, info={"description": "做法"})  # 做法
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, info={"description": "用户ID"})  # 绑定用户ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow, info={"description": "创建时间"})  # 创建时间

    # 反向关系
    user = db.relationship('User', back_populates='food')
    images = db.relationship('Image', back_populates='food', cascade="all, delete-orphan")
    cate = db.relationship("FoodCate", back_populates="food", cascade="all, delete-orphan")
    ingredient = db.relationship("FoodIngredient", back_populates="food", cascade="all, delete-orphan")


    def __repr__(self):
        return f'<Food {self.name}>'




class Image(db.Model):
    __tablename__ = 'image'  # 表名

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    url = db.Column(db.String(200), nullable=False)  # 图片 URL
    food_id = db.Column(db.Integer, db.ForeignKey('food.id'), nullable=False)

    food = db.relationship('Food', back_populates='images')

    def __repr__(self):
        return f'<Image {self.url}>'



class Cate(db.Model):
    __tablename__ = 'cate'  # 表名

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(100), nullable=False, info={"description": "分类名称"})
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, info={"description": "创建用户ID"})


    # 反向关系
    user = db.relationship('User', back_populates='cate')
    food = db.relationship("FoodCate", back_populates="cate")  # 添加此行以建立与 FoodCate 的关系

    def __repr__(self):
        return f'<Cate {self.name}>'


class Ingredient(db.Model):
    __tablename__ = 'ingredient'  # 表名

    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(100), nullable=False, info={"description": "食材名称"})
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, info={"description": "创建用户ID"})


    # 反向关系
    user = db.relationship('User', back_populates='ingredient')
    food = db.relationship("FoodIngredient", back_populates="ingredient")


    def __repr__(self):
        return f'<Ingredient {self.name}>'


class FoodCate(db.Model):
    __tablename__ = 'food_cate'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    food_id = db.Column(db.Integer, db.ForeignKey('food.id'), nullable=False)
    cate_id = db.Column(db.Integer, db.ForeignKey('cate.id'), nullable=False)

    # 可选：添加关系字段
    food = db.relationship("Food", back_populates="cate")
    cate =db.relationship("Cate", back_populates="food")


class FoodIngredient(db.Model):
    __tablename__ = 'food_ingredient'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    food_id = db.Column(db.Integer, db.ForeignKey('food.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)

    # 可选：添加关系字段
    food = db.relationship("Food", back_populates="ingredient")
    ingredient =db.relationship("Ingredient", back_populates="food")
