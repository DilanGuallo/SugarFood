#!/usr/bin/env python3
"""
Script para probar los endpoints de ratings
"""

import requests
import json

BASE_URL = "http://localhost:8000"
EMAIL = "cliente@test.com"
PASSWORD = "pass123"

def test_ratings():
    # 1. Login
    print("1. Testing login...")
    login_response = requests.post(f"{BASE_URL}/login", json={
        "email": EMAIL,
        "password": PASSWORD
    })
    print(f"   Status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print("   ❌ Login failed")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   ✅ Token obtained: {token[:50]}...")
    
    # 2. Get menus
    print("\n2. Getting menus...")
    menus_response = requests.get(f"{BASE_URL}/menus", headers=headers)
    print(f"   Status: {menus_response.status_code}")
    
    if menus_response.status_code != 200:
        print("   ❌ Failed to get menus")
        return
    
    menus_data = menus_response.json()
    menus = menus_data.get("menus", [])
    
    if not menus:
        print("   ⚠️  No menus found")
        return
    
    menu_id = menus[0].get("id")
    print(f"   ✅ Found {len(menus)} menus. Using menu ID: {menu_id}")
    
    # 3. Create a rating
    print(f"\n3. Creating rating for menu {menu_id}...")
    rating_create_response = requests.post(
        f"{BASE_URL}/menus/{menu_id}/ratings",
        headers=headers,
        json={
            "puntuacion": 5,
            "resena": "¡Excelente menú! Muy sabroso y bien presentado."
        }
    )
    print(f"   Status: {rating_create_response.status_code}")
    print(f"   Response: {rating_create_response.json()}")
    
    if rating_create_response.status_code == 200:
        print("   ✅ Rating created successfully")
    else:
        print("   ❌ Failed to create rating")
        return
    
    # 4. Get ratings for the menu
    print(f"\n4. Getting ratings for menu {menu_id}...")
    ratings_get_response = requests.get(f"{BASE_URL}/menus/{menu_id}/ratings")
    print(f"   Status: {ratings_get_response.status_code}")
    
    if ratings_get_response.status_code != 200:
        print("   ❌ Failed to get ratings")
        return
    
    ratings_data = ratings_get_response.json()
    print(f"   ✅ Ratings retrieved successfully")
    print(f"   Response: {json.dumps(ratings_data, indent=2, ensure_ascii=False)}")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_ratings()
