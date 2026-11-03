Shader "BlockOut/EffectsComposite"
{
 Properties { _MainTex ("Effects",2D)="black" {} }
 SubShader
 {
  Tags { "Queue"="Transparent" "RenderType"="Transparent" "IgnoreProjector"="True" }
  Cull Off ZWrite Off ZTest [unity_GUIZTestMode]
  Blend One OneMinusSrcAlpha
  Pass
  {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #include "UnityCG.cginc"
   struct input { float4 vertex:POSITION;float2 uv:TEXCOORD0;float4 color:COLOR; };
   struct output { float4 vertex:SV_POSITION;float2 uv:TEXCOORD0;float4 color:COLOR; };
   sampler2D _MainTex;
   output vert(input v) { output o;o.vertex=UnityObjectToClipPos(v.vertex);o.uv=v.uv;o.color=v.color;return o; }
   fixed4 frag(output i):SV_Target { fixed4 c=tex2D(_MainTex,i.uv);return c*i.color; }
   ENDCG
  }
 }
}
