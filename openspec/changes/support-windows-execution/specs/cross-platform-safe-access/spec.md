## ADDED Requirements

### Requirement: Supported platforms are declared
USW SHALL declare the platforms it supports. Linux, macOS and Windows SHALL be
supported for every documented capability, including routed handoff and both flow
layouts. A platform outside the declared set MUST fail with a clear statement that
it is unsupported, and MUST NOT partially succeed in a way that initializes a
project and then aborts on first use.

#### Scenario: A supported platform runs a flow
- **WHEN** a user runs a named flow on Linux, macOS or Windows with default configuration
- **THEN** resolution, handoff registration and execution proceed without a platform error

#### Scenario: Initialization succeeds where execution cannot follow
- **WHEN** a platform cannot support the execution path that initialization implies
- **THEN** initialization itself reports the platform as unsupported rather than succeeding first

### Requirement: One safe-access boundary with per-platform backends
Every component that reads or writes workspace state SHALL obtain filesystem
access through one shared safe-access boundary rather than calling the filesystem
directly. That boundary SHALL provide a descriptor-relative backend where the
platform supports `dir_fd`, and a pathname-based backend where it does not. Both
backends MUST enforce containment within the resolved root, reject a link or
reparse point in any component, and require the filesystem type each operation
expects. Component behavior MUST NOT differ between platforms other than in the
strength of the concurrency guarantee stated below.

#### Scenario: Platform provides descriptor-relative access
- **WHEN** the platform supports `dir_fd`
- **THEN** the boundary traverses and reads descriptor-relative and never reopens a pathname after trusting a component

#### Scenario: Platform lacks descriptor-relative access
- **WHEN** the platform does not support `dir_fd`
- **THEN** the boundary verifies every component and containment by pathname, rejects reparse points, and performs the operation without following a link

#### Scenario: Same rejection on both backends
- **WHEN** a flow root, intermediate component or final entry is a link, escapes the root, or has an unexpected filesystem type
- **THEN** both backends reject it with the same error and neither reads nor writes anything

### Requirement: A weaker platform guarantee is disclosed, never silently substituted
The descriptor-relative backend prevents a component swapped by a concurrent
process after that component was checked. The pathname-based backend cannot: it
narrows the window but cannot close it. This difference SHALL be stated in the
documentation of the safe-access boundary and in user-facing platform
documentation. USW MUST NOT describe the two backends as equivalent, and MUST NOT
present the weaker guarantee as protection against a concurrent attacker.

#### Scenario: Documentation describes safety
- **WHEN** documentation states what the safe-access boundary protects against
- **THEN** it names the platform whose guarantee is weaker and what that backend does not prevent

### Requirement: Handoff serialization does not depend on a POSIX-only primitive
The handoff lock SHALL serialize router and operation transitions on every
supported platform. It MUST NOT depend on a module or primitive that is absent on
a supported platform, and importing the handoff implementation MUST NOT fail on
any supported platform. A lock that cannot be acquired SHALL fail with a handoff
error rather than proceeding unserialized.

#### Scenario: Handoff runs on a platform without flock
- **WHEN** Begin, Outcome, Save, Finish or Cleanup runs on a platform that has no `fcntl`
- **THEN** the transition is serialized by the platform's own locking primitive and completes normally

#### Scenario: Lock cannot be acquired
- **WHEN** the handoff lock cannot be acquired within its bound
- **THEN** the operation fails with a handoff error and performs no partial transition

### Requirement: Platform support is verified, not assumed
Continuous integration SHALL run the deterministic test suite on every declared
platform. A capability claimed for a platform without a passing run on that
platform MUST NOT be documented as supported.

#### Scenario: CI runs the suite
- **WHEN** the deterministic workflow runs
- **THEN** it executes the suite on Linux and on Windows, and a failure on either is a failure of the workflow
