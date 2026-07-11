### Technical Debt

## 1
TD-005
Review FastAPI / Starlette / httpx compatibility during the next planned dependency upgrade.

post commit: 6495aab, post tag v0.0.5.2

Occurence Date: 10/07/2026

Reason:
Current dependency versions emit an upstream deprecation warning from Starlette's test client regarding future httpx changes.

Reason for postponement: 
The application code isn't using a deprecated API; the test client is.

Status:
Deferred.

Priority:
Low.


## 2
Area: Product Evaluation

Status:	Not Performed	

Reason: End-to-end developer workflow not yet convenient to exercise. Swagger is suitable for API verification but not for evaluating developer experience. Product evaluation deferred until a dedicated client/UI or practical evaluation workflow exists.