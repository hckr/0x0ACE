<?php

$host = 'http://80.233.134.207';

$opts = [
    'http' => [
        'header' => 'X-0x0ACE-Key: OoD5w68x52PGDWQenq60x4da1zZpjL7g2yXgylKbwNV9o8rAJmYROvEMkeP1aRqY'
    ]
];
$context = stream_context_create($opts);
$html = file_get_contents("$host/0x00000ACE.html", false, $context);

preg_match('/"(\/challenge?[^"]+)"/', $html, $matches);
$challenge_uri = $matches[1];


$opts = [
    'http' => [
        'header' => 'X-0x0ACE-Key: OoD5w68x52PGDWQenq60x4da1zZpjL7g2yXgylKbwNV9o8rAJmYROvEMkeP1aRqY'
    ]
];
$context = stream_context_create($opts);
file_put_contents("test.bin", file_get_contents("$host$challenge_uri", false, $context));

$r = explode(' ', trim(`g++ new_vm.cpp -o new_vm && ./new_vm test.bin`));

$content = http_build_query([
    'reg0' => $r[0],
    'reg1' => $r[1],
    'reg2' => $r[2],
    'reg3' => $r[3]
]);

echo "$content\n\n";

$opts = [
    'http' => [
        'method' => 'POST',
        'header' => "Content-type: application/x-www-form-urlencoded\r\nX-0x0ACE-Key: OoD5w68x52PGDWQenq60x4da1zZpjL7g2yXgylKbwNV9o8rAJmYROvEMkeP1aRqY",
        'content' => $content
    ]
];
$context = stream_context_create($opts);
$html = file_get_contents("$host$challenge_uri", false, $context);

echo $html . "\n";
