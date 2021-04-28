# Orchid - WebRTC P2P VPN Market (on Ethereum)
# Copyright (C) 2017-2020  The Orchid Authors

# Zero Clause BSD license {{{
#
# Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
# }}}


w_tor := 
w_tor += --disable-asciidoc
w_tor += --disable-system-torrc
w_tor += --disable-tool-name-check
w_tor += --disable-unittests

w_tor += --enable-pic

p_tor := 
l_tor := 
deps := 

# XXX: crypto_openssl_mgt.h needs to #include opensslconf.h
# (I should file this upstream, but Tor closed their Trac?)
p_tor += -DOPENSSL_NO_ENGINE

p_tor += -I@/$(pwd)/libevent/include
p_tor += -I$(CURDIR)/$(pwd)/libevent/include
deps += $(pwd)/libevent/include/event2/event-config.h
l_tor += -L@/$(pwd)/libevent/.libs
deps += $(pwd)/libevent/.libs/libevent_core.a
w_tor += tor_cv_library_zlib_dir="(system)"

p_tor += -I@/openssl/include
p_tor += -I$(CURDIR)/$(pwd)/p2p/rtc/openssl/include
deps += openssl/include/openssl/opensslconf.h
l_tor += -L@/openssl
deps += openssl/libssl.a
deps += openssl/libcrypto.a
w_tor += tor_cv_library_openssl_dir="(system)"

p_tor += -I@/$(pwd)/zlb/libz
p_tor += -I$(CURDIR)/$(pwd)/zlb/libz
l_tor += -L@/$(pwd)/zlb
deps += $(pwd)/zlb/libz.a
w_tor += tor_cv_library_zlib_dir="(system)"

ifeq ($(target),win)
l_tor += -Wl,--start-group
l_tor += -lbcrypt
l_tor += -lcrypt32
l_tor += -liphlpapi
l_tor += -lws2_32
w_tor += --disable-gcc-hardening
endif

ifeq ($(target),lnx)
# XXX: tor tries -lssl after -lpthread; I think this is a bug
l_tor += -Wl,--whole-archive
l_tor += -Wl,--allow-multiple-definition
endif

tor := 
tor += core/libtor-app.a
tor += lib/libtor-buf.a
tor += lib/libtor-compress.a
tor += lib/libtor-crypt-ops.a
tor += lib/libtor-ctime.a
tor += lib/libtor-encoding.a
tor += lib/libtor-err.a
tor += lib/libtor-evloop.a
tor += lib/libtor-fdio.a
tor += lib/libtor-fs.a
tor += lib/libtor-geoip.a
tor += lib/libtor-intmath.a
tor += lib/libtor-lock.a
tor += lib/libtor-log.a
tor += lib/libtor-malloc.a
tor += lib/libtor-math.a
tor += lib/libtor-memarea.a
tor += lib/libtor-meminfo.a
tor += lib/libtor-net.a
tor += lib/libtor-osinfo.a
tor += lib/libtor-process.a
tor += lib/libtor-pubsub.a
tor += lib/libtor-sandbox.a
tor += lib/libtor-smartlist-core.a
tor += lib/libtor-string.a
tor += lib/libtor-term.a
tor += lib/libtor-thread.a
tor += lib/libtor-time.a
tor += lib/libtor-tls.a
tor += lib/libtor-trace.a
tor += lib/libtor-version.a
tor += lib/libtor-wallclock.a
tor += lib/libcurve25519_donna.a
tor += trunnel/libor-trunnel.a
tor += ext/ed25519/donna/libed25519_donna.a
tor += ext/ed25519/ref10/libed25519_ref10.a
tor += ext/keccak-tiny/libkeccak-tiny.a
tor += lib/libtor-dispatch.a
tor += lib/libtor-container.a
tor := $(patsubst %,$(pwd)/tor/src/%,$(tor))

define _
$(output)/$(1)/$(pwd)/tor/Makefile: $(patsubst %,$(output)/$(1)/%,$(deps))
endef
$(each)

tor-c := $(shell find $(pwd)/tor -name '*.c' | LANG=C sort)

$(subst @,%,$(patsubst %,$(output)/@/%,$(tor))): $(output)/%/$(pwd)/tor/Makefile $(sysroot) $(tor-c)
	$(MAKE) -C $(dir $<) --no-print-directory src/app/tor$(exe) src/core/libtor-app.a

cflags += -I$(pwd)/tor/src
linked += $(tor)

$(call include,zlb/target.mk)
