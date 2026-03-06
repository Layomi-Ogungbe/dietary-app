CREATE TYPE meal_type_enum AS ENUM ('breakfast', 'lunch', 'dinner', 'snack');
CREATE TYPE gender_type AS ENUM ('male', 'female');
CREATE TYPE activity_level_type AS ENUM ('sedentary', 'light', 'moderate', 'vigorous');
CREATE TYPE dietary_goal_type AS ENUM ('weight_loss', 'muscle_gain', 'maintenance', 'low_sugar');

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    fullname VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    age INT,
    gender gender_type,
    weight_kg NUMERIC(5,2),
    height_cm NUMERIC(5,2),
    activity_level activity_level_type,
    dietary_goal dietary_goal_type,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    calorie_target INT,
    protein_target_g NUMERIC(5,2),
    carbs_target_g NUMERIC(5,2),
    fat_target_g NUMERIC(5,2),
    sugar_target_g NUMERIC(5,2),
    fiber_target_g NUMERIC(5,2),
    sodium_target_mg NUMERIC(7,2),
    water_target_glasses INT,
    preferred_tags TEXT[] DEFAULT '{}',
    disliked_tags TEXT[] DEFAULT '{}',
    allergies TEXT[] DEFAULT '{}',

    UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS meals (
    id SERIAL PRIMARY KEY,
    food_name VARCHAR(255) NOT NULL,
    meal_type meal_type_enum NOT NULL,
    serving_size_g INT,
    calories INT NOT NULL,
    protein_g NUMERIC(5,2),
    carbs_g NUMERIC(5,2),
    fat_g NUMERIC(5,2),
    sugar_g NUMERIC(5,2),
    fiber_g NUMERIC(5,2),
    sodium_mg NUMERIC(7,2),
    tags TEXT[] DEFAULT '{}',
    allergens TEXT[] DEFAULT '{}'

);

CREATE TABLE IF NOT EXISTS user_meal_logs (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_id INT REFERENCES meals(id) ON DELETE SET NULL,
    meal_name VARCHAR(255) NOT NULL,
    servings FLOAT NOT NULL DEFAULT 1,
    calories INT NOT NULL,
    protein_g NUMERIC(5,2),
    carbs_g NUMERIC(5,2),
    fat_g NUMERIC(5,2),
    sugar_g NUMERIC(5,2),
    fiber_g NUMERIC(5,2),
    sodium_mg NUMERIC(7,2),
    log_date DATE NOT NULL,
    time_logged TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_daily_logs (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    calories INT NOT NULL,
    protein_g NUMERIC(5,2),
    carbs_g NUMERIC(5,2),
    fat_g NUMERIC(5,2),
    sugar_g NUMERIC(5,2),
    fiber_g NUMERIC(5,2),
    sodium_mg NUMERIC(7,2),
    water_glasses INT,
    log_date TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_id, log_date)
);