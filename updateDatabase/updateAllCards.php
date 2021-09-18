<?php
/**
Usage: php.exe updateAllCards.php
	The URL used to update the local database is from ygoprodeck
	Can add arguments -S http:127.0.0.1:8000 to host locally
	phpinfo() shows php variables
	set up config in windows by changing either php.ini-development or php.ini-production to php-ini, and then 
		uncommenting:
			extension_dir = "ext"
			extension=openssl
	After generating allcards.json, update specific cards as listed in altArtCards.txt
**/

$json = file_get_contents('https://db.ygoprodeck.com/api/v7/cardinfo.php');

$array = json_decode($json, TRUE);

$fp = fopen('allcards.json', 'w');
fwrite($fp, json_encode($array));
fclose($fp);

?>