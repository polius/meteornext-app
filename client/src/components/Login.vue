<template>
  <v-content :style="{ backgroundImage: 'url(' + require('@/assets/bg.jpg') + ')', backgroundRepeat: 'no-repeat', backgroundSize: 'cover' }">
    <v-container grid-list-xl text-xs-center style="padding-top:0px;">
      <v-layout row wrap>
        <v-flex xs6 offset-xs3>
          <v-slide-y-transition mode="out-in">
            <v-card class="ma-5 pa-1" style="border-radius:5px;">
              <v-card-text>
                <v-avatar :size="150" style="margin-top:10px;"><img :src="require('../assets/logo.png')" /></v-avatar>
                <div class="display-2" style="margin-top:10px; margin-bottom:30px;"><b>Meteor</b> Next</div>
                <v-text-field box v-model="username" name="username" label="Username" required append-icon="person"></v-text-field>
                <v-text-field box v-model="password" name="password" label="Password" required append-icon="lock" type="password"></v-text-field>
                <router-link to="/" style="text-decoration:none;"><v-btn type="submit" color="info" large block style="margin-top:0px;">Login</v-btn></router-link>
              </v-card-text>
            </v-card>
          </v-slide-y-transition>
        </v-flex>
      </v-layout>
    </v-container>
  </v-content>
</template>

<script>
  export default {
    data: () => ({
      username: '',
      password: ''
    })
  }
</script>