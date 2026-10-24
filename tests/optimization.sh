#!/usr/bin/env bash
set -euo pipefail
java --list-modules > /tmp/modules.txt
for module in java.compiler jdk.compiler jdk.javadoc jdk.jlink jdk.jdi jdk.jshell java.instrument java.desktop; do grep -E "^$module@" /tmp/modules.txt; done
jimage verify "$JAVA_HOME/lib/modules"
for module in "$JAVA_HOME"/jmods/*.jmod; do jmod describe "$module" > /dev/null; done
jlink --module-path "$JAVA_HOME/jmods" --add-modules java.base,java.compiler,jdk.compiler --compress=zip-9 --output /tmp/linked-smoke
/tmp/linked-smoke/bin/java -version
/tmp/linked-smoke/bin/javac -version
printf 'System.out.println("jshell-ok");\n/exit\n' | jshell --feedback concise > /tmp/jshell.log
grep jshell-ok /tmp/jshell.log
jdb -version
java -Xshare:dump -XX:SharedArchiveFile=/tmp/smoke-cds.jsa
java -Xshare:on -XX:SharedArchiveFile=/tmp/smoke-cds.jsa -version
node <<'JS'
const assert = require('node:assert');
const session = new (require('node:inspector').Session)();
session.connect();
session.post('Runtime.evaluate', {expression:'21*2'}, (err, response) => {
  assert.ifError(err); assert.equal(response.result.value, 42); session.disconnect();
});
assert.equal(new Intl.DateTimeFormat('zh-CN').resolvedOptions().locale, 'zh-CN');
const z = require('node:zlib');
assert.equal(z.gunzipSync(z.gzipSync('hello')).toString(), 'hello');
JS
if [[ "$1" = build ]]; then
  cd /tmp
  cat > JniSmoke.java <<'JAVA'
public class JniSmoke {
  static { System.loadLibrary("jni_smoke"); }
  static native int answer();
  public static void main(String[] args) {
    if (answer() != 42) throw new AssertionError();
    System.out.println("jni-ok");
  }
}
JAVA
  javac -h /tmp JniSmoke.java
  cat > jni_smoke.c <<'C'
#include "JniSmoke.h"
JNIEXPORT jint JNICALL Java_JniSmoke_answer(JNIEnv *env, jclass cls) { return 42; }
C
  gcc -shared -fPIC -I"$JAVA_HOME/include" -I"$JAVA_HOME/include/linux" jni_smoke.c -o libjni_smoke.so
  java -Djava.library.path=/tmp JniSmoke | grep jni-ok
fi
echo "PASS optimization capabilities $1"
