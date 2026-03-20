I will search for the key changes in Node.js 22 LTS and provide a concise summary in Korean.
Node.js 22 LTS(코드명 'Jod')의 주요 변경사항을 요약해 드립니다.

**1. 성능 최적화**
*   **V8 엔진 12.4 업그레이드:** `Array.fromAsync()`, `Set` 메서드 등 최신 자바스크립트 기능을 지원합니다.
*   **Maglev 컴파일러:** 새로운 JIT 컴파일러가 기본 활성화되어 특히 단기 실행 프로그램의 성능이 향상되었습니다.
*   **Stream 성능 개선:** 기본 `highWaterMark`가 64KB로 상향되어 대용량 데이터 처리 속도가 빨라졌습니다.

**2. 개발 편의성 강화**
*   **네이티브 WebSocket:** 라이브러리 없이 표준 `WebSocket` 클라이언트를 기본으로 사용할 수 있습니다.
*   **`node --run`:** `package.json` 스크립트를 `npm run`보다 빠르게 실행할 수 있는 명령이 추가되었습니다.
*   **네이티브 Glob 지원:** `fs` 모듈에서 별도 라이브러리 없이 `glob`, `globSync`로 파일 패턴 검색이 가능합니다.
*   **Watch 모드 안정화:** `--watch` 플래그가 정식 기능으로 안정화되었습니다.

**3. 모듈 시스템 및 보안**
*   **ESM의 `require()` 지원:** 실험적으로 동기적 ES 모듈을 `require()`로 불러올 수 있어 CJS와 ESM 간 호환성이 개선되었습니다.
*   **권한 모델 개선:** 파일/네트워크 접근 권한을 더 세밀하게 제어하는 보안 기능이 강화되었습니다.

Node.js 22는 2027년 4월까지 지원되는 LTS 버전입니다.
