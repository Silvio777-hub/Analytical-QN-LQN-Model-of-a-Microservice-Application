# Project Explanation: Analytical Queueing Network Model of a Microservice Application

This document provides a comprehensive, structured explanation of the entire project. It is designed to be used as a study guide, a script for an academic presentation, or a reference for defending your methodologies in the Software Performance Engineering (SPE) module.

---

## 1. The Core Problem Solved (The "Why")

**The Problem:**
Modern cloud-native applications are constructed as directed acyclic graphs of loosely coupled microservices. When user traffic spikes, queueing delays occur at shared resources (like CPU threads or database connections), causing the entire system to slow down. Traditionally, software engineers find the saturation points by running brute-force load tests, which are computationally expensive, slow, and cannot easily predict the effect of topological changes (like adding a new replica).

**The Solution:**
This project replaces brute-force load testing with **Mathematical Analytical Modeling** based on **Queueing Theory**. We built an Open Queueing Network (QN) model of the system that can instantly predict response times, identify bottleneck services, and calculate the exact moment the system will crash under heavy load. By solving mathematical equations in milliseconds, we achieved the predictive power of a load test without actually needing to generate the load.

---

## 2. What the Project Is (High-Level Summary)

This project is an **End-to-End Performance Engineering Pipeline**. The workflow consists of:
1. Deploying a real 11-service e-commerce benchmark application (Google Online Boutique).
2. Hooking it up to a live observability stack (Prometheus, Jaeger, OpenTelemetry).
3. Harvesting real-world telemetry data (service times and routing probabilities).
4. Feeding that data into a custom-built Python mathematical solver (Mean Value Analysis).
5. Wrapping the solver in a REST API and Web Dashboard for interactive "What-If" capacity planning.

---

## 3. How It Works: The Three Pillars

### Pillar 1: Infrastructure & Observability (The Data Gatherers)
To build a mathematical model, we first need accurate parameters. We deployed the system using Docker-Compose and utilized an advanced monitoring stack:
*   **Locust Load Generator:** Simulated continuous, randomized user traffic browsing the store and adding items to carts.
*   **Prometheus & cAdvisor:** Scraped raw hardware metrics. We used these to find the CPU utilization of each container and the global arrival rate ($\lambda$) entering the system.
*   **Jaeger (Distributed Tracing):** This was the most critical tool. OpenTelemetry tracks the exact lifecycle of a request as it jumps from service to service. By parsing Jaeger traces programmatically, we were able to calculate two vital metrics:
    1.  **Routing Probabilities ($P_{i,j}$):** Out of 100 requests to the Frontend, how many go to the Currency Service? (Answer: ~18%). We mapped these transitions to build the $11 \times 11$ Routing Matrix.
    2.  **Exclusive Service Demands ($S_i$):** If the Frontend takes 200ms to respond, but spent 84ms waiting for the Checkout service, the *exclusive* processing time is only 116ms. Jaeger allowed us to subtract child spans from parent spans to find the true CPU demand.

### Pillar 2: The Analytical Model (The Mathematical Brain)
Once the parameters were collected, we constructed the queueing model:
*   **Open Queueing Network (QN):** The system was modeled as an open network because requests enter from the outside world (users), traverse the 11 services, and eventually exit. 
*   **M/M/1 Queues:** Each of the 11 microservices was mathematically represented as an M/M/1 queue. This assumes that requests arrive according to a Poisson process (Markovian arrivals) and that the service times are Exponentially distributed.
*   **M/M/c Extension:** To simulate Kubernetes Horizontal Pod Autoscaling, we extended the math to M/M/c, where $c$ is the number of container replicas. We used the **Erlang-C formula** to calculate the probability that a request must wait in the queue when multiple servers are available.
*   **Mean Value Analysis (MVA) Solver:** Instead of solving massive, complex Markov chains, we wrote a Python solver based on traffic equations. It calculates the internal arrival rates ($\lambda_i$) using linear algebra `(I - P.T) * lambda = lambda_0`, and then applies Little's Law to find utilization ($\rho$) and response times ($R$).

### Pillar 3: The Automation & API (The Product)
The engineering implementation wraps the complex math in an accessible interface:
*   **Automation Scripts (`run_all.py`):** A fully automated pipeline that fetches the Jaeger/Prometheus data, cleans it, solves the MVA model, and uses `matplotlib` to generate utilization curves and error heatmaps.
*   **FastAPI Backend & Hub UI:** We created the *SPE Observatory Hub*. A user can use the UI or send a JSON payload to the REST API asking, *"What happens if 15 users/sec arrive and I have 3 replicas of the Frontend?"* and the API instantly returns the predicted latencies.

---

## 4. Key Findings & Results (What We Discovered)

The model yielded several critical insights about the Google Online Boutique architecture:

1.  **Identification of the Bottleneck:** The math definitively proved the **Frontend** service is the primary bottleneck. Because it acts as a fan-out gateway (calling multiple backends sequentially), it reaches a high utilization ($58\%$ at $5\text{ req/s}$) much faster than the lightweight backend services.
2.  **The Saturation Point:** The model accurately predicted the theoretical maximum throughput. If external traffic hits **$\approx 8.62\text{ requests per second}$**, the Frontend utilization ($\rho$) hits 100%. At this point, the queues explode to infinity, and the system crashes.
3.  **Horizontal Scaling Validation:** Using the Erlang-C formula for M/M/c queues, we proved that scaling the Frontend to just 2 replicas ($c=2$) mathematically stabilizes the system. At $10\text{ req/s}$, an M/M/1 Frontend crashes, but an M/M/2 Frontend handles the load smoothly with a stable response time of $174.8\text{ ms}$.
4.  **High Predictive Accuracy:** When we compared our mathematical predictions to the *actual* measured times in Jaeger, our prediction for the Frontend was exceptionally accurate, with an error rate of only **3.1%**.

---

## 5. Analysis of Deviations (Why wasn't it 100% perfect?)

While the bottleneck was predicted accurately, some lightly loaded backend services showed higher percentage errors (e.g., predicted 4ms, actual 7ms). This was expected and provides a great discussion point for the report:
*   **Network Transit Time:** The M/M/1 model only accounts for CPU processing. It ignores the $1-3\text{ms}$ it takes for a packet to travel across the Docker virtual network.
*   **Serialization Overhead:** gRPC Protocol Buffers take CPU cycles to encode/decode, adding latent overhead not fully captured in the core service demand.
*   **Heavy-Tailed Distributions:** The math assumes exponential service times, but real-world cloud applications often exhibit heavy-tailed distributions (where a few requests take a very long time due to garbage collection or thread contention), increasing the average wait time.

---

## 6. Best "Talking Points" to Impress Examiners

If defending this project, use these phrases to demonstrate deep engineering comprehension:

*   *"We didn't just build a theoretical model on paper; we built a bridge between live OpenTelemetry distributed traces and mathematical queueing theory."*
*   *"We proved that M/M/1 queueing assumptions, while mathematically simple, are remarkably accurate and completely viable for predicting bottlenecks in modern REST/gRPC microservices."*
*   *"Our custom API enables 'What-If' capacity planning. We can predict the exact effect of Black Friday traffic spikes without having to spin up expensive AWS servers to run a load test."*
*   *"By identifying that the Frontend holds connections synchronously, we discovered that our open QN model could be further improved in the future by using Layered Queueing Networks (LQN) to model software-level thread contention."*
