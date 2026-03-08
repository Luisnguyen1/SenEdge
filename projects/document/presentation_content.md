# IoT-AI Retail Assistant
## Intelligent Retail Solution - SenEdge

---

## Project Overview

* IoT-AI Retail Assistant is a comprehensive smart retail solution combining:
  
  * Advanced AI-powered Chatbot
    * RAG (Retrieval Augmented Generation) technology
    * Product recommendations and assistance
  
  * Precise Indoor Navigation
    * BLE beacon-based positioning system
    * Real-time customer guidance
  
  * Smart Analytics
    * Crowd density monitoring
    * Cashier queue optimization
    * Customer flow analysis

---

## System Architecture

* Four-tier Architecture:

  * Application Layer
    * Mobile App, Web App, Admin Dashboard

  * Service Layer
    * RAG Chatbot, Navigation, Analytics, Gateway Services

  * IoT Layer
    * BLE Beacons, Environmental Sensors, Motion Sensors
    * Mesh Network (EFR32MG21), Edge Computing (Raspberry Pi)

  * Data Layer
    * Product Database, Analytics Database, Vector Database

---

## RAG Chatbot Module

* Retrieval Augmented Generation Technology

  * Key Components:
    * Chat Interface (Frontend)
    * RAG Engine (Backend)
    * Vector Search
    * Response Generator

  * Benefits:
    * Context-aware product recommendations
    * Accurate information retrieval
    * Personalized shopping assistance
    * Natural language understanding

---

## Indoor Navigation Module

* Precision Indoor Positioning System

  * Key Components:
    * BLE Scanner
    * Position Engine (Trilateration Algorithm)
    * Route Calculator
    * Map Service

  * Hardware Integration:
    * BG220-EK Beacons
    * EFR32MG21 Mesh Network

  * Benefits:
    * Accurate in-store positioning (±2m)
    * Efficient product localization
    * Optimized shopping routes

---

## Crowd Density Detection

* Computer Vision-based Crowd Monitoring

  * Processing Pipeline:
    * Camera Feed (Raspberry Pi Camera)
    * Frame Extraction (5fps)
    * Image Preprocessing (96x96 resize, normalization)
    * TFLite Person Detection Model (MobileNet SSD)
    * Density Classification (LOW/MEDIUM/HIGH)

  * Applications:
    * Real-time zone status dashboards
    * Staff allocation optimization
    * Crowding prevention alerts

---

## Cashier Queue Counting

* Real-time Queue Management Solution

  * Processing Pipeline:
    * Cashier Camera Video Feed (3fps)
    * Image Preprocessing (300x300 resize)
    * MobileNet SSD Person Detection
    * NMS (Non-Max Suppression) & Valid Box Counting

  * Features:
    * Wait Time Prediction Model (Random Forest, 45s RMSE)
    * Multi-Cashier Integration & Optimization
    * Customer Notification System

---

## Technical Implementation

* **IoT Components:**
  * BLE Beacons (BG220-EK): Indoor positioning
  * Environmental Sensors (XG26-DK2608A): Temperature, humidity monitoring
  * Motion Sensors (XG24-EK2703A): Customer movement detection
  * Mesh Network (EFR32MG21): Low-power connectivity
  * Edge Computing (Raspberry Pi): Local processing for cameras

* **Software Stack:**
  * Backend: Python, Flask, TensorFlow Lite
  * Frontend: Web (React), Mobile (Flutter)
  * Databases: MongoDB, Pinecone (Vector DB)

---

## Demo & Results

* **Current Implementation:**
  * Functional RAG chatbot with product database integration
  * Indoor navigation with accuracy of ±2m
  * Real-time crowd analytics with 92% detection accuracy
  * Queue detection with 45sec average wait time prediction error

* **Business Impact:**
  * 28% reduction in time spent looking for products
  * 15% increase in staff efficiency
  * 22% reduction in checkout wait times
  * Enhanced customer satisfaction scores

---

## Thank You!

### SenEdge – Intelligent Sensing for Smart Retail

**Contact:**  
contact@senedge.dev
