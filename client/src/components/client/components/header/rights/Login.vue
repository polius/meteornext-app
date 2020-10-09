<template>
  <div style="height:100%; margin:6% 15% 10% 15%">
    <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Login Information</div>
    <v-card>
      <v-card-text style="padding-left:20px;">
        <v-text-field label="Username" required></v-text-field>
        <v-text-field label="Password" required style="padding-top:0px;"></v-text-field>
        <v-text-field label="Hostname" required style="padding-top:0px;"></v-text-field>
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