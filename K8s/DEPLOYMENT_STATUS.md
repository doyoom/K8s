# EKS 배포 현황 및 전체 구조 정리

## 📊 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    EKS 클러스터                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐             │
│  │   WAS (API)      │─────▶│     Kafka        │             │
│  │  (logging-system)│      │     (kafka)      │             │
│  │  - was-deployment│      │  - streaming-    │             │
│  │  - 2 replicas    │      │    cluster       │             │
│  └──────────────────┘      │  - 3 brokers     │             │
│                            │  - streaming-    │             │
│                            │    topic         │             │
│                            └────────┬─────────┘             │
│                                     │                        │
│                            ┌────────▼─────────┐             │
│                            │   Spark App      │             │
│                            │   (default)      │             │
│                            │  - Consumer      │             │
│                            └──────────────────┘             │
│                                                               │
│  ┌──────────────────┐                                       │
│  │ Log Generator    │  (선택적 - 별도 로그 생성)            │
│  │ (logging-system) │                                       │
│  └──────────────────┘                                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## ✅ 배포 완료된 리소스

### 1. Kafka 인프라
- ✅ **Strimzi Operator** (`kafka` 네임스페이스)
  - `strimzi-cluster-operator` 배포됨
- ✅ **Kafka Cluster** (`kafka` 네임스페이스)
  - `streaming-cluster` - 3개 브로커 실행 중
  - Service: `streaming-cluster-kafka-bootstrap` (9092)
- ✅ **Kafka Topic** (`kafka` 네임스페이스)
  - `streaming-topic` - 3 partitions, 3 replicas

### 2. Spark 인프라
- ✅ **Spark Operator** (`spark-operator` 네임스페이스)
  - `spark-operator-controller` 배포됨
  - `spark-operator-webhook` 배포됨

### 3. WAS (Web Application Server)
- ✅ **WAS Deployment** (`logging-system` 네임스페이스)
  - `was-deployment` - 2 replicas
  - Image: `ji0513ji/log-generator:1.1.1`
  - Port: 8080
- ✅ **WAS Service (내부)**
  - `was-service` - ClusterIP (포트 80)
- ✅ **WAS Service (외부)**
  - `was-service-external` - NodePort (포트 30080)

## ✅ 추가 배포 완료 리소스

### 1. Log Generator
- ✅ **Log Generator Deployment** (`logging-system` 네임스페이스)
  - `log-generator` - 1 replica
  - Image: `ji0513ji/log-generator:1.1.1`
  - Kafka 연결: `kafka.logging-system.svc.cluster.local:9092` (수정 필요)

### 2. Spark Application
- ✅ **Spark ServiceAccount** (`default` 네임스페이스)
  - `spark` - Spark Application 실행 권한
- ✅ **Spark ConfigMap** (`default` 네임스페이스)
  - `spark-app-code` - Spark 스트리밍 코드 저장
  - Kafka 주소 수정 완료: `streaming-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092`
  - Topic 수정 완료: `streaming-topic`
- ✅ **Spark Application** (`default` 네임스페이스)
  - `spark-kafka-consumer` - Kafka에서 데이터 소비 및 처리
  - Kafka 주소 수정 완료: `streaming-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092`

## 🔧 수정 완료 사항

### 1. Spark Application Kafka 주소 수정 ✅
- 수정 전: `kafka.logging-system.svc.cluster.local:9092`
- 수정 후: `streaming-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092`

### 2. Spark ConfigMap Kafka 주소 및 Topic 수정 ✅
- Kafka 주소 수정 완료
- Topic 수정: `delivery_log` → `streaming-topic`

## 📋 배포 순서 (모두 완료)

1. ✅ Kafka 인프라 (완료)
2. ✅ Spark Operator (완료)
3. ✅ WAS (완료)
4. ✅ Spark ServiceAccount 배포 (완료)
5. ✅ Spark ConfigMap 배포 및 수정 (완료)
6. ✅ Spark Application 배포 및 수정 (완료)
7. ✅ Log Generator 배포 (완료)

## 🌐 네임스페이스 구조

- `kafka`: Kafka 클러스터 및 관련 리소스
- `spark-operator`: Spark Operator
- `logging-system`: WAS 및 Log Generator
- `default`: Spark Application

## 🔗 서비스 연결 정보

### Kafka 접속
- 내부: `streaming-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092`
- Topic: `streaming-topic`

### WAS 접속
- 내부: `was-service.logging-system.svc.cluster.local:80`
- 외부: `<노드IP>:30080`

