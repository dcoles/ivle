BASEDIR=/home/informatics

CONFIGS =	config/lite.conf \
			config/svn-apache.conf

SCRIPTS =	scripts/mkJail.sh \
			scripts/safe-python

#JAILRULE = redhat_el5_x86_64
#JAILRULE = ubuntu_gibbon_i686
JAILRULE = centos_4_i686

.PHONY : install
install : $(CONFIGS) $(SCRIPTS) $(JAILRULE)
	cp $(CONFIGS) $(BASEDIR)/config
	cp $(SCRIPTS) $(BASEDIR)/bin

.PHONY : $(BASEDIR)
$(BASEDIR) :
	-mkdir $(BASEDIR)
	-mkdir $(BASEDIR)/bin
	-mkdir $(BASEDIR)/config
	-mkdir $(BASEDIR)/config/jail
	-mkdir $(BASEDIR)/jails
	-mkdir $(BASEDIR)/svn
	-mkdir $(BASEDIR)/www
	-mkdir $(BASEDIR)/www/home
	-mkdir $(BASEDIR)/www/public

.PHONY : redhat_el5_x86_64
redhat_el5_x86_64 : $(BASEDIR)
	-mkdir $(BASEDIR)/config/jail/lib64
	cp /lib64/ld-linux-x86-64.so.2 /lib64/ld-linux-x86-64.so.2
	cp /lib64/libc.so.6 $(BASEDIR)/config/jail/lib64/libc.so.6
	cp /lib64/libdl.so.2 $(BASEDIR)/config/jail/lib64/libdl.so.2
	cp /lib64/libm.so.6 $(BASEDIR)/config/jail/lib64/libm.so.6
	cp /lib64/libpthread.so.0 $(BASEDIR)/config/jail/lib64/libpthread.so.0
	cp /lib64/libutil.so.1 $(BASEDIR)/config/jail/lib64/libutil.so.1
	-mkdir $(BASEDIR)/config/jail/usr
	-mkdir $(BASEDIR)/config/jail/usr/bin
	cp /usr/bin/python2.4 $(BASEDIR)/config/jail/usr/bin/python2.4
	ln -s $(BASEDIR)/config/jail/usr/bin/python2.4 \
		$(BASEDIR)/config/jail/usr/bin/python
	-mkdir $(BASEDIR)/config/jail/usr/lib64
	cp /usr/lib64/libpython2.4.so.1.0 \
		$(BASEDIR)/config/jail/usr/lib64/libpython2.4.so.1.0
	-mkdir $(BASEDIR)/config/jail/usr/lib
	-mkdir $(BASEDIR)/config/jail/usr/lib/python2.4
	cp -r /usr/lib/python2.4 $(BASEDIR)/config/jail/usr/lib/

.PHONY : centos_4_i686
centos_4_i686 : $(BASEDIR)
	-mkdir $(BASEDIR)/config/jail/lib
	-mkdir $(BASEDIR)/config/jail/lib/tls
	cp /lib/ld-linux.so.2 $(BASEDIR)/config/jail/lib
	cp /lib/libcom_err.so.2 $(BASEDIR)/config/jail/lib/
	cp /lib/libcrypto.so.4 $(BASEDIR)/config/jail/lib/
	cp /lib/libdl.so.2 $(BASEDIR)/config/jail/lib
	cp /lib/libgcc_s.so.1 $(BASEDIR)/config/jail/lib/
	cp /lib/libresolv.so.2 $(BASEDIR)/config/jail/lib/
	cp /lib/libssl.so.4 $(BASEDIR)/config/jail/lib/
	cp /lib/libutil.so.1 $(BASEDIR)/config/jail/lib
	cp /lib/tls/libc.so.6 $(BASEDIR)/config/jail/lib/tls
	cp /lib/tls/libm.so.6 $(BASEDIR)/config/jail/lib/tls
	cp /lib/tls/libpthread.so.0 $(BASEDIR)/config/jail/lib/tls
	-mkdir $(BASEDIR)/config/jail/usr
	-mkdir $(BASEDIR)/config/jail/usr/bin
	cp /usr/local/bin/python2.5 $(BASEDIR)/config/jail/usr/bin/python2.5
	ln -s $(BASEDIR)/config/jail/usr/bin/python2.5 \
		$(BASEDIR)/config/jail/usr/bin/python
	-mkdir $(BASEDIR)/config/jail/usr/lib
	cp /usr/lib/libfreetype.so.6 $(BASEDIR)/config/jail/usr/lib
	cp /usr/lib/libgssapi_krb5.so.2 $(BASEDIR)/config/jail/usr/lib/
	cp /usr/lib/libk5crypto.so.3 $(BASEDIR)/config/jail/usr/lib/
	cp /usr/lib/libkrb5.so.3 $(BASEDIR)/config/jail/usr/lib/
	cp /usr/lib/libpng12.so.0 $(BASEDIR)/config/jail/usr/lib
	cp /usr/lib/libstdc++.so.6 $(BASEDIR)/config/jail/usr/lib
	cp /usr/lib/libz.so.1 $(BASEDIR)/config/jail/usr/lib/
	-mkdir $(BASEDIR)/config/jail/usr/lib/python2.5
	cp -r /usr/local/lib/python2.5 $(BASEDIR)/config/jail/usr/lib/

.PHONY : ubuntu_gibbon_i686
ubuntu_gibbon_i686 : $(BASEDIR)
	-mkdir $(BASEDIR)/config/jail/lib
	cp /lib/ld-linux.so.2 \
		$(BASEDIR)/config/jail/lib/ld-linux.so.2 
	-mkdir $(BASEDIR)/config/jail/lib/tls
	-mkdir $(BASEDIR)/config/jail/lib/tls/i686
	-mkdir $(BASEDIR)/config/jail/lib/tls/i686/cmov
	cp /lib/tls/i686/cmov/libc.so.6 \
		$(BASEDIR)/config/jail/lib/tls/i686/cmov/libc.so.6
	cp /lib/tls/i686/cmov/libdl.so.2 \
		$(BASEDIR)/config/jail/lib/tls/i686/cmov/libdl.so.2
	cp /lib/tls/i686/cmov/libm.so.6 \
		$(BASEDIR)/config/jail/lib/tls/i686/cmov/libm.so.6
	cp /lib/tls/i686/cmov/libpthread.so.0 \
		$(BASEDIR)/config/jail/lib/tls/i686/cmov/libpthread.so.0
	cp /lib/tls/i686/cmov/libutil.so.1 \
		$(BASEDIR)/config/jail/lib/tls/i686/cmov/libutil.so.1
	-mkdir $(BASEDIR)/config/jail/usr
	-mkdir $(BASEDIR)/config/jail/usr/bin
	cp /usr/bin/python2.5 \
		$(BASEDIR)/config/jail/usr/bin/python2.5
	ln -s $(BASEDIR)/config/jail/usr/bin/python2.5 \
		$(BASEDIR)/config/jail/usr/bin/python
	-mkdir $(BASEDIR)/config/jail/usr/lib
	-mkdir $(BASEDIR)/config/jail/usr/lib/python2.5
	cp -r /usr/lib/python2.5 $(BASEDIR)/config/jail/usr/lib/
