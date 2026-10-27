using System;
using HarmonyLib;

namespace MimirMod
{
    [HarmonyPatch(typeof(Chat), "InputText")]
    internal static class Chat_InputText_Patch
    {
        private static bool Prefix(Chat __instance)
        {
            var input = __instance.m_input;
            if (input == null || string.IsNullOrEmpty(input.text))
                return true;

            string text = input.text.TrimStart();
            string cmd = MimirPlugin.Command.Value;

            bool isCommand =
                text.Equals(cmd, StringComparison.OrdinalIgnoreCase) ||
                text.StartsWith(cmd + " ", StringComparison.OrdinalIgnoreCase);

            if (!isCommand)
                return true;

            string question = text.Length > cmd.Length ? text.Substring(cmd.Length).Trim() : "";

            input.text = "";

            string who = Player.m_localPlayer != null ? Player.m_localPlayer.GetPlayerName() : "Você";
            __instance.AddString("<color=#9ad0ff>" + who + "</color>: " + text);

            MimirPlugin.Instance.Ask(__instance, question);

            return false;
        }
    }
}
