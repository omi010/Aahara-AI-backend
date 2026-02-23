from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from aahara.routes import user_routes, meal_routes
from aahara.database import engine, Base, SessionLocal
from aahara.models.user import User
from aahara.models.meal import Meal
from aahara.schemas.user import UserCreate, UserResponse, UserLogin, Token
from aahara.security import hash_password, verify_password, create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from aahara.models.food import FoodLog
from datetime import date,timedelta
from sqlalchemy import func
from aahara.utils.calorie_engine import estimate_calories
from aahara.models.weight import WeightLog
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app = FastAPI(
    title="Aahara AI",
    description="Know Your Food.",
    version="1.0.0"
)

app.include_router(user_routes.router)
app.include_router(meal_routes.router)


@app.get("/")
def root():
    return {"message": "Aahara AI Backend Running Successfully 🚀"}

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Welcome to Aahara AI"}


@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pwd = hash_password(user.password)

    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_pwd
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()

    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password):
        db.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.email})

    db.close()

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }

@app.post("/add-food")
def add_food(
    food_name: str,
    calories: int,
    quantity: str,
    meal_type: str,
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()

    new_food = FoodLog(
        food_name=food_name,
        calories=calories,
        quantity=quantity,
        meal_type=meal_type,
        log_date=date.today(),
        user_id=current_user.id
    )

    db.add(new_food)
    db.commit()
    db.refresh(new_food)
    db.close()

    return {"message": "Food added successfully"}

@app.get("/today-calories")
def get_today_calories(current_user: User = Depends(get_current_user)):
    db = SessionLocal()

    total = db.query(func.sum(FoodLog.calories)).filter(
        FoodLog.user_id == current_user.id,
        FoodLog.log_date == date.today()
    ).scalar()

    db.close()

    return {
        "date": str(date.today()),
        "total_calories": total or 0
    }

@app.get("/meals")
def get_all_meals(current_user: User = Depends(get_current_user)):
    db = SessionLocal()

    meals = db.query(FoodLog).filter(
        FoodLog.user_id == current_user.id
    ).order_by(FoodLog.id.desc()).all()

    db.close()

    return meals

@app.delete("/meal/{meal_id}")
def delete_meal(meal_id: int, current_user: User = Depends(get_current_user)):
    db = SessionLocal()

    meal = db.query(FoodLog).filter(
        FoodLog.id == meal_id,
        FoodLog.user_id == current_user.id
    ).first()

    if not meal:
        db.close()
        raise HTTPException(status_code=404, detail="Meal not found")

    db.delete(meal)
    db.commit()
    db.close()

    return {"message": "Meal deleted successfully"}

@app.put("/meal/{meal_id}")
def update_meal(
    meal_id: int,
    food_name: str,
    calories: int,
    quantity: str,
    meal_type: str,
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()

    meal = db.query(FoodLog).filter(
        FoodLog.id == meal_id,
        FoodLog.user_id == current_user.id
    ).first()

    if not meal:
        db.close()
        raise HTTPException(status_code=404, detail="Meal not found")

    meal.food_name = food_name
    meal.calories = calories
    meal.quantity = quantity
    meal.meal_type = meal_type

    db.commit()
    db.refresh(meal)
    db.close()

    return {"message": "Meal updated successfully"}

@app.post("/estimate-calories")
def estimate(text: str, current_user: User = Depends(get_current_user)):
    total = estimate_calories(text)

    return {
        "input": text,
        "estimated_calories": total
    }

@app.get("/weekly-calories")
def weekly_calories(current_user: User = Depends(get_current_user)):
    db = SessionLocal()

    seven_days_ago = date.today() - timedelta(days=6)

    results = db.query(
        FoodLog.log_date,
        func.sum(FoodLog.calories).label("total_calories")
    ).filter(
        FoodLog.user_id == current_user.id,
        FoodLog.log_date >= seven_days_ago
    ).group_by(
        FoodLog.log_date
    ).order_by(
        FoodLog.log_date
    ).all()

    db.close()

    return [
        {
            "date": str(row.log_date),
            "total_calories": row.total_calories
        }
        for row in results
    ]

@app.put("/set-goal")
def set_daily_goal(
    goal: int,
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()

    user = db.query(User).filter(User.id == current_user.id).first()
    user.daily_goal = goal

    db.commit()
    db.refresh(user)
    db.close()

    return {
        "message": "Daily goal updated",
        "daily_goal": goal
    }

@app.get("/goal-progress")
def goal_progress(current_user: User = Depends(get_current_user)):
    db = SessionLocal()

    today_total = db.query(func.sum(FoodLog.calories)).filter(
        FoodLog.user_id == current_user.id,
        FoodLog.log_date == date.today()
    ).scalar() or 0

    user = db.query(User).filter(User.id == current_user.id).first()

    remaining = user.daily_goal - today_total

    db.close()

    return {
        "daily_goal": user.daily_goal,
        "consumed_today": today_total,
        "remaining_calories": remaining
    }

@app.put("/update-body")
def update_body_metrics(
    height_cm: int,
    weight_kg: int,
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()

    user = db.query(User).filter(User.id == current_user.id).first()
    user.height_cm = height_cm
    user.weight_kg = weight_kg

    db.commit()
    db.refresh(user)
    db.close()

    return {
        "message": "Body metrics updated",
        "height_cm": height_cm,
        "weight_kg": weight_kg
    }

@app.get("/bmi")
def calculate_bmi(current_user: User = Depends(get_current_user)):
    db = SessionLocal()

    user = db.query(User).filter(User.id == current_user.id).first()

    if not user.height_cm or not user.weight_kg:
        db.close()
        raise HTTPException(status_code=400, detail="Height and weight not set")

    height_m = user.height_cm / 100
    bmi = round(user.weight_kg / (height_m ** 2), 2)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    db.close()

    return {
        "height_cm": user.height_cm,
        "weight_kg": user.weight_kg,
        "bmi": bmi,
        "category": category
    }

@app.post("/log-weight")
def log_weight(
    weight_kg: int,
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()

    new_entry = WeightLog(
        weight_kg=weight_kg,
        user_id=current_user.id
    )

    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    db.close()

    return {
        "message": "Weight logged successfully",
        "weight_kg": weight_kg
    }

@app.get("/weight-history")
def weight_history(current_user: User = Depends(get_current_user)):
    db = SessionLocal()

    records = db.query(WeightLog).filter(
        WeightLog.user_id == current_user.id
    ).order_by(
        WeightLog.log_date
    ).all()

    db.close()

    return [
        {
            "date": str(r.log_date),
            "weight_kg": r.weight_kg
        }
        for r in records
    ]

@app.get("/dashboard")
def dashboard(current_user: User = Depends(get_current_user)):
    db = SessionLocal()

    today = date.today()
    seven_days_ago = today - timedelta(days=6)

    # Today calories
    today_total = db.query(func.sum(FoodLog.calories)).filter(
        FoodLog.user_id == current_user.id,
        FoodLog.log_date == today
    ).scalar() or 0

    # 7-day calorie average
    week_data = db.query(
        FoodLog.log_date,
        func.sum(FoodLog.calories).label("total")
    ).filter(
        FoodLog.user_id == current_user.id,
        FoodLog.log_date >= seven_days_ago
    ).group_by(FoodLog.log_date).all()

    if week_data:
        avg_calories = round(
            sum(row.total for row in week_data) / len(week_data), 2
        )
    else:
        avg_calories = 0

    # Weight change (last 7 days)
    weights = db.query(WeightLog).filter(
        WeightLog.user_id == current_user.id,
        WeightLog.log_date >= seven_days_ago
    ).order_by(WeightLog.log_date).all()

    if len(weights) >= 2:
        weight_change = weights[-1].weight_kg - weights[0].weight_kg
    else:
        weight_change = 0

    # BMI
    user = db.query(User).filter(User.id == current_user.id).first()

    if user.height_cm and user.weight_kg:
        height_m = user.height_cm / 100
        bmi = round(user.weight_kg / (height_m ** 2), 2)
    else:
        bmi = None

    remaining = user.daily_goal - today_total

    db.close()

    return {
        "today_calories": today_total,
        "daily_goal": user.daily_goal,
        "remaining_calories": remaining,
        "average_calories_7_days": avg_calories,
        "weight_change_7_days": weight_change,
        "current_bmi": bmi
    }