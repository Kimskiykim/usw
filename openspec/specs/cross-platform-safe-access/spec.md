# Спецификация cross-platform-safe-access

## Purpose
Определяет объявленный набор поддерживаемых платформ, единую safe-access
boundary с backends под платформу, обязательное раскрытие более слабой
гарантии там, где descriptor-relative access недоступен, независимость
сериализации handoff от POSIX-only primitive и проверку поддержки платформ
прогоном deterministic suite.

## Requirements

### Requirement: Поддерживаемые платформы объявлены явно
USW SHALL объявлять платформы, которые он поддерживает. Linux, macOS и Windows
SHALL поддерживаться для каждой документированной capability, включая routed
handoff и оба flow layout. Платформа вне объявленного набора MUST завершаться
ошибкой с явным сообщением о неподдерживаемости и MUST NOT частично
срабатывать так, что проект инициализируется, а первый же запуск прерывается.

#### Scenario: Поддерживаемая платформа запускает flow
- **WHEN** пользователь запускает именованный flow на Linux, macOS или Windows
  с конфигурацией по умолчанию
- **THEN** разрешение, регистрация handoff и execution проходят без platform
  error

#### Scenario: Инициализация проходит там, где execution не сможет
- **WHEN** платформа не может поддержать execution path, который подразумевает
  инициализация
- **THEN** сама инициализация сообщает платформу как неподдерживаемую, а не
  завершается успешно первой

### Requirement: Одна safe-access boundary с backends под платформу
Каждый component, читающий или записывающий workspace state, SHALL получать
доступ к filesystem через одну общую safe-access boundary, а не обращаться к
filesystem напрямую. Эта boundary SHALL предоставлять descriptor-relative
backend там, где платформа поддерживает `dir_fd`, и pathname-based backend там,
где не поддерживает. Оба backends MUST обеспечивать containment внутри
разрешённого root, отклонять link или reparse point в любом component и
требовать filesystem type, ожидаемый каждой операцией. Поведение component MUST
NOT различаться между платформами ничем, кроме силы concurrency guarantee,
указанной ниже.

#### Scenario: Платформа предоставляет descriptor-relative access
- **WHEN** платформа поддерживает `dir_fd`
- **THEN** boundary проходит и читает descriptor-relative и никогда не открывает
  pathname повторно после признания component доверенным

#### Scenario: На платформе нет descriptor-relative access
- **WHEN** платформа не поддерживает `dir_fd`
- **THEN** boundary проверяет каждый component и containment по pathname,
  отклоняет reparse points и выполняет операцию, не следуя за link

#### Scenario: Одинаковый отказ на обоих backends
- **WHEN** flow root, intermediate component или final entry является link,
  выходит за пределы root либо имеет неожиданный filesystem type
- **THEN** оба backends отклоняют его с одной и той же ошибкой и ничего не
  читают и не записывают

### Requirement: Более слабая гарантия платформы раскрывается, а не подменяется молча
Descriptor-relative backend защищает от подмены component другим process после
его проверки. Pathname-based backend этого не может: он сужает окно, но не
закрывает его. Эта разница SHALL быть указана в документации safe-access
boundary и в пользовательской документации по платформам. USW MUST NOT
описывать оба backends как равнозначные и MUST NOT представлять более слабую
гарантию как защиту от concurrent attacker.

#### Scenario: Документация описывает безопасность
- **WHEN** документация утверждает, от чего защищает safe-access boundary
- **THEN** она называет платформу с более слабой гарантией и то, чего этот
  backend не предотвращает

### Requirement: Сериализация handoff не зависит от POSIX-only primitive
Handoff lock SHALL сериализовать transitions router и operation на каждой
поддерживаемой платформе. Он MUST NOT зависеть от module или primitive,
отсутствующего на поддерживаемой платформе, а import реализации handoff MUST NOT
падать ни на одной поддерживаемой платформе. Lock, который не удалось
захватить, SHALL завершаться handoff error, а не продолжать без сериализации.

#### Scenario: Handoff работает на платформе без flock
- **WHEN** Begin, Outcome, Save, Finish или Cleanup выполняется на платформе,
  где нет `fcntl`
- **THEN** transition сериализуется собственным locking primitive платформы и
  завершается нормально

#### Scenario: Lock не удаётся захватить
- **WHEN** handoff lock не удаётся захватить в отведённых границах
- **THEN** операция завершается handoff error и не выполняет частичный
  transition

### Requirement: Поддержка платформы проверяется, а не предполагается
Continuous integration SHALL прогонять deterministic test suite на каждой
объявленной платформе. Capability, заявленная для платформы без успешного
прогона на ней, MUST NOT документироваться как поддерживаемая.

#### Scenario: CI прогоняет suite
- **WHEN** выполняется deterministic workflow
- **THEN** он прогоняет suite на Linux и на Windows, а падение на любой из них
  является падением workflow
