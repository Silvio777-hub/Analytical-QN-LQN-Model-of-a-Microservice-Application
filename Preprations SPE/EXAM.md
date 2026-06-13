# Exam Questions – Software Performance Engineering

## Course Context
These questions are designed for an **Engineering Performance (SPE)** module covering the analytical modeling of microservice applications, with a focus on **Queueing Networks**, **M/M/1**, **M/M/c**, and related concepts used in the *Online Boutique* case study.

---

## 1. Fundamentals of Queueing Theory

**Q1.** What are the four basic components that define a queueing system?
- **A:** Arrival process, service process, number of servers, system capacity (queue length limit).

**Q2.** Define the traffic intensity \(\rho\) for an M/M/1 queue and explain its significance.
- **A:** \(\rho = \lambda S\), where \(\lambda\) is the arrival rate and \(S\) is the mean service time. \(\rho < 1\) is required for a stable system; as \(\rho \to 1\) the waiting time grows dramatically.

---

## 2. M/M/1 Queue

**Q3.** Write the expressions for the average number in the system \(L\) and the average response time \(R\) in an M/M/1 queue.
- **A:** \(L = \frac{\rho}{1-\rho}\) and \(R = \frac{S}{1-\rho}\) (Little’s law: \(L = \lambda R\)).

**Q4.** If a service has \(\lambda = 5\) req/s and \(S = 0.08\) s, compute \(\rho\), \(L\) and \(R\).
- **A:** \(\rho = 5 \times 0.08 = 0.40\). \(L = 0.40 / (1-0.40) = 0.667\) customers. \(R = 0.08 / (1-0.40) = 0.133\) s (133 ms).

**Q5.** Explain why the exponential service‑time assumption is often acceptable for analytical modeling of microservices.
- **A:** The exponential distribution yields a memoryless property, simplifying balance equations and allowing closed‑form solutions. For many microservices the variability is high and the tail is not dominant, making the exponential approximation a reasonable first order model.

---

## 3. M/M/c (Multi‑Server) Queue

**Q6.** Define the Erlang‑C formula for the probability that an arriving request must wait (\(P_Q\)).
- **A:** \[ P_Q = \frac{\frac{a^{c}}{c!} \frac{1}{1-\rho}}{\sum_{k=0}^{c-1} \frac{a^{k}}{k!} + \frac{a^{c}}{c!}\frac{1}{1-\rho}} \]
  where \(a = \lambda S\) (offered load) and \(\rho = a / c\).

**Q7.** For a service with \(\lambda = 8\) req/s, \(S = 0.1\) s and \(c = 2\) servers, compute \(\rho\) and the average waiting time \(W_q\).
- **A:** Offered load \(a = 8 \times 0.1 = 0.8\). \(\rho = a / c = 0.8 / 2 = 0.4\). Using Erlang‑C, \(P_Q \approx 0.095\). \(W_q = \frac{P_Q S}{c (1-\rho)} \approx \frac{0.095 \times 0.1}{2 \times 0.6} \approx 0.0079\) s (7.9 ms).

**Q8.** Discuss how increasing the number of replicas (servers) influences \(\rho\) and system response time.
- **A:** Adding replicas reduces the per‑server utilization \(\rho = a / c\). As \(\rho\) drops, both the waiting probability \(P_Q\) and waiting time \(W_q\) shrink sharply, leading to lower overall response time \(R = S + W_q\). This is the analytical basis for horizontal scaling.

---

## 4. Open Queueing Networks (QN)

**Q9.** In an open QN, how are the internal arrival rates \(\lambda_i\) computed?
- **A:** Solve the linear system \(\boldsymbol{\lambda} = \boldsymbol{\lambda_0} + P^T \boldsymbol{\lambda}\) ⇒ \((I - P^T)\boldsymbol{\lambda} = \boldsymbol{\lambda_0}\). \(\lambda_0\) contains external arrivals (only the Frontend in the Online Boutique).

**Q10.** What is the *visit ratio* \(V_i\) and how does it relate to throughput?
- **A:** \(V_i = \lambda_i / \lambda\) (average number of visits to node \(i\) per external arrival). The service demand for node \(i\) is \(D_i = V_i \times S_i\). System throughput equals the external arrival rate \(\lambda\).

**Q11.** Explain why the bottleneck service is the one with the highest utilization.
- **A:** Utilization \(U_i = \lambda_i S_i\). The service with \(U_i\) closest to 1 limits the overall throughput because it reaches saturation first, causing queueing delay to dominate the system response time.

---

## 5. Layered Queueing Networks (LQN) – Extension

**Q12.** What additional element does an LQN introduce compared to a traditional QN?
- **A:** LQNs model *software resources* (e.g., thread pools, connection pools) as separate service centers layered on top of hardware resources, allowing representation of blocking and contention within a single microservice.

**Q13.** Provide an example of a resource that can be modeled as a separate layer in the Online Boutique.
- **A:** The gRPC worker thread pool inside the Frontend service can be represented as a software‑level M/M/1 queue that feeds into the hardware CPU server.

---
## 5.1 Additional Core Concepts

### 5.1.1 Closed Queueing Networks
**Definition:** A closed queueing network contains a fixed number of jobs circulating among service centers, with no external arrivals or departures.  
**Example:** A set of 100 virtual users repeatedly issuing requests to the microservices.  
**Key Property:** Throughput is limited by the bottleneck service (Bottleneck Law).

### 5.1.2 Little’s Law
**Definition:** In any stable queueing system, $L = \lambda R$ where $L$ is the average number of jobs in the system, $\lambda$ the arrival rate, and $R$ the average response time.  
**Example:** For the M/M/1 example where $L = 0.667$ jobs and $\lambda = 5$ req/s, the response time is $R = L/\lambda = 0.133$ s, matching the formula.

### 5.1.3 Utilization Bound & Saturation
**Definition:** For an M/M/c queue, per‑server utilization is $\rho = \frac{\lambda S}{c}$. Stability requires $\rho < 1$.  
**Difference to M/M/1:** In a single‑server system $\rho = \lambda S$; adding servers divides the offered load, reducing $\rho$.

### 5.1.4 Erlang‑B vs Erlang‑C
- **Erlang‑B:** Models a loss system (no waiting queue). Probability of call blocking $B$ is given by the Erlang‑B formula. Used for telephone circuits and scenarios where requests are dropped.
- **Erlang‑C:** Models a waiting system (queues allowed). Provides the waiting probability $P_Q$ and average waiting time. Appropriate for web services where requests are queued.

### 5.1.5 Mean Value Analysis (MVA)
**Definition:** An iterative algorithm to compute performance metrics (throughput, response time, utilization) for closed queueing networks without solving large Markov chains.
**Steps:** 1) Initialise with zero load. 2) Increment population. 3) Update response times using $R_i = S_i (1 + Q_i)$, where $Q_i$ is the average number of jobs at node $i$.
**Why Useful:** Gives fast, accurate predictions for multi‑class workloads and underpins the analytical solver used in this project.

---

## 5.2 Key Metrics & Typical Thresholds

- **Utilization (\(\rho\))**: Critical when \(\rho > 0.8\); aim for \(\rho < 0.7\) to maintain headroom.
- **Response Time (R)**: Compare against SLO (e.g., 200 ms for user‑facing services). For M/M/1, $R = \frac{S}{1-\rho}$.
- **Waiting Probability (\(P_Q\))**: Acceptable if \(P_Q < 0.1\) for low‑latency services; computed with Erlang‑C for M/M/c.
- **Throughput (X)**: Must meet expected request rate; keep $X < \frac{c}{S}$ (system capacity).
- **Average Queue Length (\(L_q\))**: Keep $L_q < 5$ jobs to avoid excessive queuing delay.

### Differences Summary

| Concept | M/M/1 | M/M/c |
|--------|-------|-------|
| Servers | 1 | $c \ge 1$ |
| Utilization | $\rho = \lambda S$ | $\rho = \frac{\lambda S}{c}$ |
| Waiting Probability | 0 (no queue) | Erlang‑C formula |
| Typical Use | Simple, single‑instance services | Replicated / horizontally‑scaled services |

## 6. Practical Questions on the Project

**Q14.** Which service was identified as the primary bottleneck in the *Online Boutique* case study?
- **A:** The **Frontend** service (arrival gate) with the highest utilization.

**Q15.** How does the model account for the effect of horizontal scaling of the Frontend?
- **A:** By using an M/M/c formulation for the Frontend where the number of servers \(c\) equals the replica count; the Erlang‑C analysis yields the new utilization and response time.

**Q16.** What metric collection tools were used to obtain service‑time and routing data?
- **A:** **Prometheus** for quantitative metrics (request rates, CPU usage) and **Jaeger** for distributed tracing to extract exclusive service times and routing probabilities.

---

## 7. Quick Reference Formulas

| Symbol | Definition | Formula |
|--------|------------|---------|
| \(\lambda\) | External arrival rate | – |
| \(S_i\) | Mean service time of node *i* | – |
| \(P_{i,j}\) | Routing probability from *i* to *j* | – |
| \(\rho_i\) | Utilization of node *i* | \(\rho_i = \lambda_i S_i\) |
| \(R_i\) (M/M/1) | Mean response time | \(R_i = \frac{S_i}{1-\rho_i}\) |
| \(P_Q\) (M/M/c) | Waiting probability | Erlang‑C formula |
| \(W_q\) (M/M/c) | Waiting time | \(W_q = \frac{P_Q S}{c(1-\rho)}\) |
| \(R_{sys}\) | System end‑to‑end response time | \(R_{sys}=\sum_i V_i R_i\) |

---

*End of Exam Sheet*
