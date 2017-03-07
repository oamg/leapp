Listen 9000

<VirtualHost *:9000>

    DocumentRoot /var/www/phpmyadmin
    <Directory /var/www/phpmyadmin>
        # enable the .htaccess rewrites
        AllowOverride All
        Order allow,deny
        Allow from All
    </Directory>
</VirtualHost>
