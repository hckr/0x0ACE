<?php

$opts = [
    'http' => [
        'header' => 'X-0x0ACE-Key: OoD5w68x52PGDWQenq60x4da1zZpjL7g2yXgylKbwNV9o8rAJmYROvEMkeP1aRqY'
    ]
];
$context = stream_context_create($opts);
$html = file_get_contents('http://5.9.247.121/d34dc0d3', false, $context);

preg_match('/\[(\d+), ..., (\d+)\]/', $html, $matches);
// var_dump($matches);

$primes_str = include('primes.php');
$solution_begin = strpos($primes_str, ',' . $matches[1] . ',') + 1 + strlen($matches[1]) + 1;
$solution_end = strpos($primes_str, ',' . $matches[2] . ',');

if ($solution_begin == false || $solution_end == false) {
    die("Not enough primes. Try again.\n");
}

$solution = substr($primes_str, $solution_begin, $solution_end - $solution_begin);

preg_match('/name="verification" value="([^"]+)"/', $html, $matches);
$token = $matches[1];

$content = http_build_query([
    'solution' => $solution,
    'verification' => $token
]);

// echo urldecode($content) . "\n";

$opts = [
    'http' => [
        'method' => 'POST',
        'header' => "Content-type: application/x-www-form-urlencoded\r\nX-0x0ACE-Key: OoD5w68x52PGDWQenq60x4da1zZpjL7g2yXgylKbwNV9o8rAJmYROvEMkeP1aRqY",
        'content' => $content
    ]
];
$context = stream_context_create($opts);
$html = file_get_contents('http://5.9.247.121/d34dc0d3', false, $context);

echo $html . "\n";
