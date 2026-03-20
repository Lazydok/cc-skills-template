# Gemini Code Review: test_sample.py

## Focus Areas: SQL Injection & Cache Issues

### 1. SQL Injection 취약점 분석 및 수정 (`get_user_orders`)

*   **문제점:** `f-string`을 사용하여 `user_id`를 SQL 쿼리 문자열에 직접 삽입하고 있습니다. 만약 사용자가 `user_id` 값으로 `' OR '1'='1`과 같은 값을 전달하면, 전체 주문 테이블이 노출되는 등 데이터베이스가 공격에 취약해집니다.
*   **해결책:** 반드시 **매개변수화된 쿼리(Parameterized Query)** 또는 **준비된 문구(Prepared Statements)**를 사용해야 합니다.
*   **수정 제안:**
    ```python
    def get_user_orders(user_id, db_connection):
        # DB 라이브러리에 따라 다를 수 있지만, 일반적으로 다음과 같은 방식을 권장합니다.
        query = "SELECT * FROM orders WHERE user_id = ?"
        return db_connection.execute(query, (user_id,))
    ```

### 2. 캐시(Cache) 문제 분석 및 개선 (`OrderCache`)

*   **문제점:** `max_size` 속성은 정의되어 있으나, `set` 메서드에서 이를 확인하거나 기존 항목을 삭제(Eviction)하는 로직이 전혀 없습니다. 이로 인해 캐시가 무한히 커져 **메모리 부족(OOM)** 현상이 발생할 수 있습니다.
*   **개선 방안:** 항목을 추가하기 전에 현재 캐시 크기를 확인하고, 한도를 초과할 경우 가장 오래된 항목을 제거하는 **LRU(Least Recently Used)** 알고리즘 등을 적용해야 합니다.
*   **수정 제안:**
    ```python
    from collections import OrderedDict

    class OrderCache:
        def __init__(self, max_size=100):
            self._cache = OrderedDict() # 순서를 유지하는 딕셔너리 사용
            self.max_size = max_size

        def set(self, order_id, order):
            if order_id in self._cache:
                del self._cache[order_id]
            elif len(self._cache) >= self.max_size:
                self._cache.popitem(last=False) # 가장 오래된 항목(FIFO) 제거
            self._cache[order_id] = order
    ```

### 3. 기타 발견된 버그 및 개선 사항

*   **`process_order` 함수 내 할인 계산 오류:**
    *   **버그:** 주석에 언급된 대로 `discount`가 백분율이라면 `price * quantity - discount`는 잘못된 계산입니다. `(price * quantity) * (1 - discount/100)`과 같은 방식으로 수정되어야 합니다. 현재는 고정 금액만큼만 차감되고 있습니다.
*   **음수 합계 미방지:**
    *   **버그:** 할인이 상품 가격보다 클 경우 `total`이 음수가 될 수 있습니다. `total = max(0, total)`과 같은 안전장치가 필요합니다.
*   **세금 계산 및 반올림 부재:**
    *   **문제:** 세율(`0.1`)이 하드코딩되어 있으며, 부동 소수점 연산 결과에 대한 반올림 처리가 없어 `grand_total`이 지저분한 소수점 자릿수를 가질 수 있습니다. `round()` 함수나 `Decimal` 모듈 사용을 권장합니다.
*   **이메일 유효성 검사 미흡 (`validate_email`):**
    *   **문제:** 단순히 `@`와 `.`의 존재만 확인하므로 `a.@.b` 같은 잘못된 형식도 통과됩니다. 정규표현식(`re` 모듈)을 사용하는 것이 좋습니다.
*   **시간대(Timezone) 미지정:**
    *   **개선:** `datetime.now()`는 로컬 시간을 사용합니다. 서버 환경에서는 일관성을 위해 `datetime.now(timezone.utc)`를 사용하는 것이 표준입니다.
