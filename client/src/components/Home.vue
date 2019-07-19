<template>
  <v-container>
    <v-layout text-xs-center wrap>
      <v-flex xs12 style="margin-top:100px;">
        <v-avatar :size="200" ><v-img :src="require('../assets/logo.png')" class="my-3" contain height="200"></v-img></v-avatar>
      </v-flex>

      <v-flex mb-4 style="margin-top:30px;">
        <h1 class="display-2 font-weight-bold mb-3"><b>Meteor</b> Next</h1>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
  export default {
    data: () => ({

    })
  }
</script>