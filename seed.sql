INSERT INTO meals (food_name, meal_type, serving_size_g, calories, protein_g, carbs_g, fat_g, sugar_g, fiber_g, sodium_mg, tags, allergens) VALUES
('Porridge (made with semi-skimmed milk)', 'breakfast', 100, 75, 3.4, 10.0, 2.0, 3.6, 1.2, 35, ARRAY['breakfast','british','low-calorie','low-fat'], ARRAY['Milk']),

('Weetabix', 'breakfast', 100, 362, 12.0, 69.0, 2.0, 4.4, 10.0, 270, ARRAY['breakfast','british','high-fiber','low-fat'], ARRAY['Gluten']),

('Special K Cereal', 'breakfast', 100, 375, 7.0, 84.0, 1.5, 17.0, 1.5, 450, ARRAY['breakfast','british','high-sugar','low-fat'], ARRAY['Gluten']),

('Scrambled Eggs', 'breakfast', 100, 148, 10.0, 1.6, 11.0, 1.1, 0.0, 120, ARRAY['breakfast','british','low-calorie'], ARRAY['Eggs']),

('Toast (white bread with butter)', 'breakfast', 100, 310, 8.0, 35.0, 15.0, 3.0, 1.5, 480, ARRAY['breakfast','british'], ARRAY['Gluten','Milk']),

('Baked Beans (in tomato sauce)', 'breakfast', 100, 78, 4.8, 12.0, 0.4, 4.9, 3.7, 390, ARRAY['breakfast','british','low-calorie','low-fat'], ARRAY[]::text[]),

('Grilled Bacon', 'breakfast', 100, 325, 27.0, 1.0, 24.0, 0.0, 0.0, 1100, ARRAY['breakfast','british','high-protein'], ARRAY[]::text[]),

('Orange Juice', 'breakfast', 100, 45, 0.7, 10.0, 0.2, 8.0, 0.2, 1, ARRAY['breakfast','british','low-calorie','low-fat'], ARRAY[]::text[]),

('Chicken Sandwich', 'lunch', 100, 230, 13.0, 22.0, 9.0, 3.0, 2.5, 420, ARRAY['american','low-calorie'], ARRAY['Gluten','Eggs']),

('Ham & Cheese Sandwich', 'lunch', 100, 275, 14.0, 24.0, 12.0, 3.0, 1.5, 600, ARRAY['american'], ARRAY['Gluten','Milk']),

('Tuna Salad', 'lunch', 100, 132, 15.0, 3.0, 6.0, 1.5, 2.0, 320, ARRAY['healthy','low-calorie'], ARRAY['Fish','Eggs']),

('Vegetable Soup', 'lunch', 100, 45, 2.0, 7.5, 1.0, 3.0, 1.2, 280, ARRAY['low-calorie','low-fat','vegetarian'], ARRAY['Celery']),

('Jacket Potato with Beans', 'lunch', 100, 118, 5.0, 22.0, 0.5, 4.0, 3.5, 290, ARRAY['low-calorie','low-fat'], ARRAY[]::text[]),

('Fish and Chips', 'lunch', 100, 240, 13.0, 25.0, 9.0, 0.0, 2.5, 480, ARRAY['low-calorie'], ARRAY['Fish','Gluten']),

('Pasta Salad with Dressing', 'lunch', 100, 160, 5.0, 23.0, 5.0, 2.0, 1.5, 200, ARRAY['healthy','italian','low-calorie'], ARRAY['Gluten','Eggs']),

('Chicken Caesar Wrap', 'lunch', 100, 210, 11.0, 19.0, 9.0, 2.0, 1.5, 420, ARRAY['low-calorie'], ARRAY['Gluten','Eggs','Milk','Fish']),

('Roast Chicken with Vegetables', 'dinner', 100, 165, 25.0, 4.0, 5.0, 2.0, 1.5, 220, ARRAY['high-protein','low-calorie'], ARRAY[]::text[]),

('Spaghetti Bolognese', 'dinner', 100, 145, 7.0, 18.0, 4.5, 3.0, 1.8, 330, ARRAY['low-calorie','low-fat'], ARRAY['Gluten']),

('Cottage Pie', 'dinner', 100, 120, 8.0, 15.0, 3.5, 2.0, 1.5, 270, ARRAY['low-calorie','low-fat'], ARRAY['Milk','Celery']),

('Fish Pie', 'dinner', 100, 140, 9.0, 12.0, 6.0, 1.0, 1.2, 290, ARRAY['low-calorie'], ARRAY['Fish','Milk']),

('Vegetable Stir Fry (with noodles)', 'dinner', 100, 100, 3.0, 17.0, 2.0, 3.5, 2.5, 280, ARRAY['asian','low-calorie','low-fat','vegetarian'], ARRAY['Gluten','Soya']),

('Grilled Salmon with Rice', 'dinner', 100, 190, 19.0, 8.0, 9.0, 1.0, 0.8, 120, ARRAY['high-protein','low-calorie'], ARRAY['Fish']),

('Beef Curry with Rice', 'dinner', 100, 175, 12.0, 16.0, 6.0, 2.0, 1.5, 360, ARRAY['indian','low-calorie'], ARRAY[]::text[]),

('Vegetarian Lasagne', 'dinner', 100, 150, 6.0, 17.0, 6.0, 3.0, 2.0, 310, ARRAY['low-calorie','vegetarian'], ARRAY['Gluten','Milk','Eggs']),

('Pizza Margherita', 'dinner', 100, 270, 11.0, 31.0, 10.0, 3.0, 2.0, 610, ARRAY['italian'], ARRAY['Gluten','Milk']),

('Chicken Tikka Masala with Rice', 'dinner', 100, 180, 14.0, 12.0, 6.0, 2.5, 1.5, 350, ARRAY['indian','low-calorie'], ARRAY['Milk']);