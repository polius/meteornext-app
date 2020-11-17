<template>
  <div style="height:100%; overflow-y:auto;">
    <!----------------->
    <!-- SERVER INFO -->
    <!----------------->
    <v-container style="width:70%; position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); overflow-y:auto;">
      <v-layout wrap>
        <v-flex v-show="item.length == 0" xs12>
          <div class="body-2" style="text-align:center; margin-top:1%;">Select a server to show the details</div>
        </v-flex>
        <v-flex v-show="item.length != 0">
          <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Server details</div>
          <v-card>
            <v-card-text style="padding:23px 20px 5px 20px">
              <!-- <v-row justify="space-around" style="margin-top:2%">
                <div class="text-h6" style="font-weight:400"><v-icon small :color="item.region_shared ? 'error' : 'warning'" style="font-size:20px; margin-right:10px; margin-bottom:2px;">{{ item.region_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>{{ item.region }}</div>
              </v-row> -->
              <v-row no-gutters>
                <v-col cols="8" style="padding-right:10px">
                  <v-text-field v-model="item.name" readonly label="Name" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
                <v-col cols="4" style="padding-left:10px">
                  <v-text-field v-model="item.region" readonly label="Region" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
              </v-row>
              <!-- SQL -->
              <v-row no-gutters>
                <v-col cols="8" style="padding-right:10px">
                  <v-text-field v-model="item.engine" readonly label="Engine" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
                <v-col cols="4" style="padding-left:10px">
                  <v-text-field v-model="item.version" readonly label="Version" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
              </v-row>
              <v-row no-gutters style="margin-top:10px;">
                <v-col cols="8" style="padding-right:10px">
                  <v-text-field v-model="item.hostname" readonly label="MySQL Hostname" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
                <v-col cols="4" style="padding-left:10px">
                  <v-text-field v-model="item.port" readonly label="Port" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
              </v-row>
              <v-text-field v-model="item.username" readonly label="Username" required style="padding-top:0px; font-size:1rem;"></v-text-field>
              <v-text-field v-model="item.password" readonly label="Password" style="padding-top:0px; font-size:1rem;"></v-text-field>
              <!-- SSH -->
              <v-row no-gutters style="margin-top:15px;">
                <v-col cols="8" style="padding-right:10px">
                  <v-text-field v-model="item.hostname" readonly label="SSH Hostname" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
                <v-col cols="4" style="padding-left:10px">
                  <v-text-field v-model="item.port" readonly label="Port" required style="padding-top:0px; font-size:1rem;"></v-text-field>
                </v-col>
              </v-row>
              <v-text-field v-model="item.username" readonly label="Username" required style="padding-top:0px; font-size:1rem;"></v-text-field>
              <v-text-field v-model="item.password" readonly label="Password" style="padding-top:0px; font-size:1rem;"></v-text-field>
            </v-card-text>
          </v-card>
        </v-flex>
      </v-layout>
    </v-container>
  </div>
</template>

<script>
import { mapFields } from '../../js/map-fields'

export default {
  data() {
    return {
      image: {'MySQL': 'mysql', 'Aurora MySQL': 'amazon_aurora'}
    }
  },
  computed: {
    ...mapFields([
      'sidebarSelected'
    ], { path: 'client/connection' }),
    item: function() {
      if (this.sidebarSelected.length == 0) return []
      else return this.sidebarSelected[this.sidebarSelected.length - 1]
    },
  },
  watch: {
    sidebarSelected (val) {
      if (val) {
        console.log(val)
      }
    },
  },
}
</script>