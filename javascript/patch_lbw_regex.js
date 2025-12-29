/*
 * extensions/sd-webui-lora-block-weight-ui/javascript/patch_lbw_regex.js
 *
 * オリジナルの extraNetworks.js の正規表現を上書きし、
 * :lbw=... 構文に対応させます。
 */

// オリジナルの extraNetworks.js で定義されている変数を、
// ユーザー指定の正規表現で上書きします。
var re_extranet = /<([^:^>]+:[^:]+):[\d.]+(?::[^>]+)?>(.*)/;
var re_extranet_g = /<([^:^>]+:[^:]+):[\d.]+(?::[^>]+)?>/g;
var re_extranet_neg = /\(([^:^>]+:[\d.]+(?::[^)]+)?)\)/;
var re_extranet_g_neg = /\(([^:^>]+:[\d.]+(?::[^)]+)?)\)/g;

console.log("[sd-webui-lora-block-weight-ui] extraNetworks.js regex patched for LBW syntax.");
