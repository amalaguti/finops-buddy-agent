# aws-edge-platform Specification

## Purpose

Define **in-repository** expectations for the **reference AWS deployment** of FinOps Buddy: edge security (WAF, TLS, OIDC), compute (ECS Fargate, ECR), logging, and IAM access to **Bedrock**—so operators can implement a **standard, sensitive-data-appropriate** public URL for internal users.

## ADDED Requirements

### Requirement: Reference deployment documentation exists

The project SHALL include **reference deployment documentation** (under `docs/` or a path documented in the README) that describes: placement of **AWS WAF** in front of an **internet-facing Application Load Balancer**, **HTTPS (TLS)** termination on the ALB, **OIDC authentication** integrated with the ALB listener so unauthenticated users cannot reach the application, an **ECS Fargate** service as the target group, **Amazon ECR** as the container registry, and use of the **ECS task IAM role** for AWS API calls including **Amazon Bedrock** inference (with **VPC endpoints or documented egress** as appropriate).

#### Scenario: Documentation names WAF and OIDC at the edge

- **WHEN** a reader opens the reference deployment document
- **THEN** the document explicitly describes **WAF** and **ALB OIDC** (or equivalent ALB authenticate action) as the edge controls before traffic reaches the service

#### Scenario: Documentation names Fargate and ECR

- **WHEN** a reader opens the reference deployment document
- **THEN** the document states that application containers run on **Amazon ECS using Fargate** and that images are stored in **ECR**

#### Scenario: Documentation addresses streaming and load balancing

- **WHEN** a reader opens the reference deployment document
- **THEN** the document addresses **Server-Sent Events** and/or long-lived HTTP connections and SHALL state whether **target group stickiness** (or an alternative such as a single task) is required for correct behavior when more than one task is running

### Requirement: Infrastructure-as-code scaffold for the reference architecture

The project SHALL include an **IaC scaffold** (e.g. a root module under `infra/` or `terraform/`) with a **README** listing **required inputs** (examples: VPC/subnets, **ACM certificate ARN**, **OIDC issuer URL**, **client id/secret** references or SSM/Secrets Manager ARNs, domain name) and **outputs** or references needed to wire the ALB to ECS. The scaffold SHALL be **placeholder-safe** (no real account IDs or secrets committed).

#### Scenario: IaC README lists OIDC and certificate inputs

- **WHEN** a contributor opens the IaC README
- **THEN** the README lists **OIDC** parameters and **TLS certificate** (or ACM) as required inputs for the public HTTPS listener

#### Scenario: IaC enables ALB and WAF logging

- **WHEN** a contributor inspects the scaffold for observability resources
- **THEN** the scaffold includes or explicitly documents enabling **ALB access logs** and **WAF logging** (destination may be S3 or CloudWatch per team standard)

### Requirement: Cross-account trust pattern is documented

The reference documentation SHALL describe the **hub role** pattern: the **ECS task execution/task role** (or a dedicated **FinOps hub role** assumed by the task) is **trusted by** FinOps **reader roles** in member accounts via **STS AssumeRole**, and those reader roles grant **least-privilege** access needed for Cost Explorer and related read-only FinOps APIs used by the app.

#### Scenario: Documentation mentions AssumeRole into member accounts

- **WHEN** a reader reviews the cross-account section of the deployment document
- **THEN** the document explains that the application obtains credentials for a member account using **STS AssumeRole** from the task’s **IAM role** (or documented dedicated role)
