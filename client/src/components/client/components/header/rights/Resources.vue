<template>
  <div style="height:100%; margin:6% 15% 10% 15%">
    <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Resource Limits</div>
    <v-card>
      <v-card-text style="padding-left:20px;">
        <v-text-field label="Max Queries / hour" required></v-text-field>
        <v-text-field label="Max Updates / hour" required style="padding-top:0px;"></v-text-field>
        <v-text-field label="Max Connections / hour" required style="padding-top:0px;"></v-text-field>
        <v-text-field label="Max Simultaneous Connections / hour" required style="padding-top:0px;"></v-text-field>
        <div class="body-2">Remarks: 0 (default) = no limit</div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>

export default {
  data() {
    return {
    }
  },
  computed: {
  },
  methods: {

  }
}
</script>