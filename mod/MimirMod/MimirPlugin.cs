using System;
using System.Collections;
using System.Text;
using BepInEx;
using BepInEx.Configuration;
using HarmonyLib;
using UnityEngine;
using UnityEngine.Networking;

namespace MimirMod
{
    [BepInPlugin(GUID, "Mímir - Valheim Wiki Oracle", "0.1.0")]
    public class MimirPlugin : BaseUnityPlugin
    {
        public const string GUID = "com.flipneves.mimir";

        public static MimirPlugin Instance;
        public static ConfigEntry<string> ApiUrl;
        public static ConfigEntry<string> UrlSource;
        public static ConfigEntry<string> ApiKey;
        public static ConfigEntry<string> Command;

        private Harmony _harmony;

        private void Awake()
        {
            Instance = this;

            ApiUrl = Config.Bind("API", "Url", "http://localhost:8000",
                "Endereço base da API do Mímir (usado quando UrlSource está vazio).");
            UrlSource = Config.Bind("API", "UrlSource", "",
                "Opcional. URL crua que retorna o endereço atual da API (ex.: raw de um Gist/arquivo no GitHub). Se preenchido, tem prioridade sobre Url.");
            ApiKey = Config.Bind("API", "ApiKey", "",
                "Chave de API (header X-API-Key). Deixe vazio se a API for local sem auth.");
            Command = Config.Bind("Chat", "Command", "/mimir",
                "Prefixo que invoca o Mímir no chat. Ex.: /mimir como consigo bronze?");

            _harmony = new Harmony(GUID);
            _harmony.PatchAll();

            Logger.LogInfo("Mímir despertou. Use " + Command.Value + " <pergunta> no chat.");
        }

        private void OnDestroy()
        {
            _harmony?.UnpatchSelf();
        }

        public void Ask(Chat chat, string question)
        {
            if (chat == null) chat = Chat.instance;
            if (chat == null) return;

            if (string.IsNullOrWhiteSpace(question))
            {
                Say(chat, "Fala, viajante — o que desejas saber?");
                return;
            }

            Say(chat, "<i>medita sobre a tua pergunta...</i>");
            StartCoroutine(AskRoutine(chat, question));
        }

        private IEnumerator AskRoutine(Chat chat, string question)
        {
            string baseUrl = ApiUrl.Value;

            if (!string.IsNullOrEmpty(UrlSource.Value))
            {
                string src = UrlSource.Value + (UrlSource.Value.Contains("?") ? "&" : "?") + "t=" + DateTime.UtcNow.Ticks;
                using (var res = UnityWebRequest.Get(src))
                {
                    res.timeout = 20;
                    yield return res.SendWebRequest();
                    if (res.result != UnityWebRequest.Result.Success)
                    {
                        Say(chat, "As águas de Mímisbrunnr estão turvas... (não encontrei o portal: " + res.error + ")");
                        yield break;
                    }
                    string resolved = (res.downloadHandler.text ?? "").Trim();
                    if (resolved.Length > 0)
                        baseUrl = resolved.Split('\n')[0].Trim().Trim('"');
                }
            }

            string url = baseUrl.TrimEnd('/') + "/rag/ask";
            string body = JsonUtility.ToJson(new AskRequest { question = question });

            using (var req = new UnityWebRequest(url, "POST"))
            {
                req.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(body));
                req.downloadHandler = new DownloadHandlerBuffer();
                req.SetRequestHeader("Content-Type", "application/json");
                if (!string.IsNullOrEmpty(ApiKey.Value))
                    req.SetRequestHeader("X-API-Key", ApiKey.Value);
                req.timeout = 120;

                yield return req.SendWebRequest();

                bool failed = req.result != UnityWebRequest.Result.Success;
                if (failed)
                {
                    Say(chat, "As águas de Mímisbrunnr estão turvas... (" + req.error + ")");
                    yield break;
                }

                string answer = null;
                try
                {
                    answer = JsonUtility.FromJson<AskResponse>(req.downloadHandler.text)?.answer;
                }
                catch (Exception e)
                {
                    Logger.LogError("Falha ao ler resposta: " + e);
                }

                Say(chat, string.IsNullOrEmpty(answer)
                    ? "Não recebi resposta clara das águas."
                    : answer);
            }
        }

        private static void Say(Chat chat, string text)
        {
            chat.AddString("<color=#FFD54A>Mímir</color>: " + text);
        }

        [Serializable]
        private class AskRequest { public string question; }

        [Serializable]
        private class AskResponse { public string answer; }
    }
}
